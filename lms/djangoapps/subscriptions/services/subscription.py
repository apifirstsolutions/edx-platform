
from common.djangoapps.student.models import CourseEnrollment
import logging
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
import stripe
from django.forms import ValidationError

from openedx.core.djangoapps.enrollments.api import add_enrollment
from openedx.core.djangoapps.catalog.utils import get_course_uuid_for_course
from common.djangoapps.entitlements.models import CourseEntitlement
from common.djangoapps.course_modes.models import CourseMode

from ..models import BillingCycles, License, Statuses, Subscription, SubscriptionPlan, Transactions, SubscriptionTransaction
from .ecommerce import (
  create_ecommerce_product, 
  create_stockrecord, 
  update_ecommerce_product, 
  update_stockrecord_price,
  get_stripe_customer_id,
)
from ..helpers.unique_slugify import unique_slugify
from ..helpers.stripe_utils import get_billing_cycle_anchor

from lms.envs.common import (
  STRIPE_API_KEY,
  STRIPE_CURRENCY,
  STRIPE_TAX_RATE_ID,
)

log = logging.getLogger(__name__)
stripe.api_key = STRIPE_API_KEY
class SubscriptionService:
  
  # Creates a Product and Prices in Stripe.
  # Creates an Ecommerce Product with prices as product variants.
  
  # product
  #
  # prices = { 
  #   'month': decimal, 
  #   'year': decimal,
  #   'onetime': decimal,
  # }
  #
  # user, from request

  def create_product(self, plan, prices, user):
    unique_slugify(plan, plan.name)
    try:
      # Create Stripe Product
      stripe_product = stripe.Product.create(name=plan.name,)
      result = {
        'stripe_product_id': stripe_product.id
      }
      
      # Create Ecommrce Product
      ecommerce_product = create_ecommerce_product(user, plan)
      result['ecommerce_prod_id'] = ecommerce_product.get('id')
      
      for cycle in prices.keys():

        if prices[cycle] is not None:
          
          if cycle is not 'onetime':
            # Create Stripe Price
            price = stripe.Price.create(
              unit_amount= int(prices[cycle] * 100),
              currency=STRIPE_CURRENCY,
              recurring={ 'interval': cycle },
              product=stripe_product.id,
            )
            result['stripe_price_id_' + cycle] = price.id

          # Create Ecommerce Product Variants to set differcent prices.
          ecommerce_product_variant = create_ecommerce_product(user, plan, parent_id=ecommerce_product.get('id'), cycle=cycle)
          result['ecommerce_prod_id_' + cycle] = ecommerce_product_variant.get('id')
          
          sku = plan.slug + '-' + cycle
          stockrecord = create_stockrecord(user, ecommerce_product_variant.get('id'), sku, prices[cycle])
          result['ecommerce_stockrecord_id_' + cycle] = stockrecord.get('id')

      return result

    except Exception as e:
      log.warning(u"Error occured while creating product in Stripe or Ecommerce. %s", str(e))
      raise

  
  # Updates a Product name and Prices in Stripe.
  # Updates an Ecommerce Product with multiple prices options.

  # FIXME use kwargs
  def update_product(self, user, plan, new_prices, new_product_name=None, new_description=None, new_valid_until=None): 
    result = {}

    try:
      if new_product_name is not None:
        stripe.Product.modify(plan.stripe_prod_id, name=new_product_name)

      for cycle in new_prices.keys():
        
        if new_prices[cycle] is not None:

          if cycle is not 'onetime':
            price = stripe.Price.create(
              unit_amount= int(new_prices[cycle] * 100),
              currency=STRIPE_CURRENCY,
              recurring={ 'interval': cycle },
              product=plan.stripe_prod_id,
            )
            result['stripe_price_id_' + cycle] = price.id

          stockrecord_id = getattr(plan, 'ecommerce_stockrecord_id_'+cycle)
          
          if stockrecord_id is not None:
            update_stockrecord_price(user, stockrecord_id, new_prices[cycle])
          else:
            # create new stockrecord
            sku = plan.slug + '-' + cycle
            create_stockrecord(user, plan.ecommerce_prod_id, sku, new_prices[cycle])
    
      # None means no change of values
      if new_product_name is not None or new_description is not None or new_valid_until is not None:
        update_ecommerce_product(user, plan.ecommerce_prod_id, new_product_name, new_description, new_valid_until)

      return result
    
    except Exception as e:
      raise

  def _enroll_user_to_bundled_courses(self, user, bundle):
    try:
      for course in bundle.courses.all():
        course_mode = CourseMode.objects.get(course_id=course.id)
        add_enrollment(user.username, str(course.id), mode=course_mode.slug)
    except Exception as e:
      log.error("Error enrolling user to bundled course.")
      raise


  # If using Stripe - after first payment, create a Stripe subscription with Price (from subscription plan)
  # custome can either be user or enterprise
  def create_subscription(self, subscription, stripe_customer_id=None):
    result = {
      'stripe_customer_id': None,
      'stripe_subscription_id': None,
      'stripe_invoice_id': None,
      'stripe_price_id': None,
    }

    onetime_pay = subscription.billing_cycle == BillingCycles.ONE_TIME.value
   
    if not onetime_pay and subscription.user is not None:

      price_id = getattr(subscription.subscription_plan, 'stripe_price_id_' + subscription.billing_cycle)
      result['stripe_price_id'] = price_id

      try:
        
        if stripe_customer_id is None:
          stripe_customer_id = get_stripe_customer_id(subscription.user)
        
        billing_cycle_anchor = get_billing_cycle_anchor(subscription.start_at)
       
        sub = stripe.Subscription.create(
          customer=stripe_customer_id,
          billing_cycle_anchor=billing_cycle_anchor,
          proration_behavior='none',
          items=[{ "price": price_id }],
          default_tax_rates=[ STRIPE_TAX_RATE_ID ],
          cancel_at=int(subscription.subscription_plan.valid_until.timestamp())
        )

        result['stripe_customer_id'] = stripe_customer_id
        result['stripe_subscription_id'] = sub.id
        result['stripe_invoice_id'] = sub.latest_invoice

        self._enroll_user_to_bundled_courses(subscription.user, subscription.subscription_plan.bundle)
        
      except Exception as e:
        log.error(u"Error occured creating Subscription in Stripe. %s", str(e))
        raise
  
    return result
  
  # For Enterprise users, assign course entitlements and license for active subscriptions
  def assign_licenses_n_entitlements(self, user, subscription):
    
    try:
      # check if sub. license count is not exceeded, assign  a license if not
      active_licenses_count = License.objects.filter(subscription=subscription).count()
      
      if active_licenses_count < subscription.license_count:
        License.objects.get_or_create(user=user, subscription=subscription)

      else:
        log.error(u"License count exceeded for subcription. %s", subscription.id)
        raise Exception("License count exceeded.")

      # get all bundled courses related to a subscription and assign course entitlements for user
      plan = SubscriptionPlan.objects.filter(id=subscription.subscription_plan.id)
      
      for course in plan.bundle.courses.all():
        course_uuid = get_course_uuid_for_course(str(course.id))
        course_mode = CourseMode.objects.get(course_id=course.id)
        CourseEntitlement.objects.get_or_create(user_id=user.id, course_uuid=course_uuid, mode=course_mode.slug)

    except Exception as e:
      log.error(u"Error assigning License and entitlements of enterprise user - %s", user.username)
      raise

  # Check if can change license count for enterprise subscription
  def validate_license_count_change(self, subscription):
    if subscription.enterprise is not None:
      used_licenses_count = License.objects.filter(subscription__id=subscription.id).count()
      if used_licenses_count > subscription.license_count:
        raise ValidationError(u"There are already %s licenses used on this Subscription.", used_licenses_count)



  def cancel_enrollments_entitlements(self, subscription):
    # TODO - sets subscription status to CANCELLED
    # enrollment = CourseEnrollment.objects.get(user_id=subscription.user.id, )
    
    # set student_courseenrollment is_active=false for all courses in the plan
    # set expire date to now() of user course entitlements  for all courses in the plan
    # handle enterprise
    pass

  # Cancels a subscriptions
  # Deletes a Stripe subscription and record in Transactions
  def cancel_subscription(self, subscription):

    try:
      if subscription.user is not None:
        stripe.Subscription.delete(subscription.stripe_subscription_id)
        
      self.cancel_enrollments_entitlements(subscription)
      self.record_transaction(subscription, SubscriptionTransaction.CANCEL.value)

      return { 'success': True }
    except Exception as e:
      log.error(u"Error occured cancelling Subscription in Stripe. %s", str(e))
      raise

  # Update all subscriptions cancel_at time when sub. plan valid_until change
  def update_subscriptions_validity_in_plan(self, plan):
    
    subscriptions = Subscription.objects.filter(subscription_plan_id=plan.id)

    for subscription in subscriptions:
      if subscription.stripe_subscription_id is not None:
        stripe.Subscription.modify(
          subscription.stripe_subscription_id,
          cancel_at=int(plan.valid_until.timestamp())
        )

  # TODO - 
  # (1) After firstpayment is detected from webhook, update the current subscription and next billing date
  # (2) On expiration, update subscription status and subs. history
  # (3) On cancellation, update subscription status and subs. history
  # (2) Create a Stripe subscription with Price (from subscription plan)
  def renew_subscription(self, next_billing_date):
    # set student_courseenrollment is_active=true for all courses in the plan
    # set expire date to null of user course entitlements  for all courses in the plan
    # record transaction
    pass


  # TODO - 
  # Check Stripe Subscriptions status for payments and transaction information (like invoices)
  # make necessary subscription status updates
  def check_subscription(self, subscription_id):
    pass


  # record transations when subscription status changes
  def record_transaction(self, subscription, action, stripe_invoice_id=None, ecommerce_order_number=None):
    Transactions.objects.create(
      subscription=subscription, 
      status=subscription.status, 
      description=action, 
      license_count=subscription.license_count,
      stripe_invoice_id=stripe_invoice_id,
      ecommerce_order_number=ecommerce_order_number,
    )

    