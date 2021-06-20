
import logging
import stripe
from bridgekeeper import perms
from datetime import datetime

from django.forms import ValidationError
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.entitlements.models import CourseEntitlement
from common.djangoapps.course_modes.models import CourseMode
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.enrollments.api import add_enrollment
from openedx.core.djangoapps.catalog.utils import get_course_uuid_for_course
from enterprise.models import EnterpriseCustomerUser

from ..models import (
  BillingCycles, 
  License, 
  Statuses, 
  Subscription, 
  SubscriptionPlan, 
  SubscriptionTransaction,
  Transactions, 
)
from .ecommerce import (
  create_ecommerce_product, 
  create_stockrecord, 
  update_ecommerce_product, 
  update_stockrecord_price,
  get_stripe_customer_id,
)
from ..permissions import (
    SUBSCRIBE_TO_PLAN,
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
  #
  # prices = { 
  #   'month': decimal, 
  #   'year': decimal,
  #   'onetime': decimal,
  # }
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
        
        if plan.ecommerce_prod_id_month is not None:
          update_ecommerce_product(user, plan.ecommerce_prod_id_month, new_product_name, new_description, new_valid_until)
        if plan.ecommerce_prod_id_year is not None:
          update_ecommerce_product(user, plan.ecommerce_prod_id_year, new_product_name, new_description, new_valid_until)
        if plan.ecommerce_prod_id_onetime is not None:
          update_ecommerce_product(user, plan.ecommerce_prod_id_onetime, new_product_name, new_description, new_valid_until)
        
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


  # Create a Stripe subscription and enroll users
  def create_subscription(self, subscription, stripe_customer_id=None):

    if not perms[SUBSCRIBE_TO_PLAN].check(subscription.user, subscription.subscription_plan):
      raise Exception("Permission error. Cannot subscribe to plan")

    result = {
      'stripe_customer_id': None,
      'stripe_subscription_id': None,
      'stripe_invoice_id': None,
      'stripe_price_id': None,
    }

    onetime = subscription.billing_cycle == BillingCycles.ONE_TIME.value
   
    if not onetime and subscription.user is not None:

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

  # For enterprise subscription, check that new license count is not less than the used licenses
  def validate_license_count_change(self, subscription):
    if subscription.enterprise is not None:
      used_licenses_count = License.objects.filter(subscription__id=subscription.id).count()
      if used_licenses_count > subscription.license_count:
        raise ValidationError(u"There are already %s licenses used on this Subscription.", used_licenses_count)

  # Set all enrollments to sub. plan courses to is_active=false
  # Set all entitlements to sub. plan courses to expire date to now()
  def _cancel_enrollments_entitlements(self, subscription):
    plan_course_ids = subscription.subscription_plan.bundle.courses.values('id')
    plan_course_uuids = list(map(lambda id: get_course_uuid_for_course(str(id)), plan_course_ids))
    
    if subscription.user is not None:
      # Public user case
      enrollments = CourseEnrollment.objects.filter(user_id=subscription.user.id, course_id__in=plan_course_ids)
      entitlements = CourseEntitlement.objects.filter(user_id=subscription.user.id, course_uuid__in=plan_course_uuids) 
    
    elif subscription.enterprise is not None:
      # enterprise case
      enterprise_user_ids = EnterpriseCustomerUser.objects.filter(enterprise_customer_id=subscription.enterprise.uuid).values('user_id')
      enrollments = CourseEnrollment.objects.filter(user_id__in=enterprise_user_ids, course_id__in=plan_course_ids)
      entitlements = CourseEntitlement.objects.filter(user_id__in=enterprise_user_ids, course_uuid__in=plan_course_uuids)
    
    else:
      raise Exception("Subscription is neither for public or enterprise")

    for enrollment in enrollments:
        enrollment.is_active = False
        try:
          enrollment.save()
        except:
          log.error("Unable to cancel enrollment id %s" % (enrollment.id))
          pass

    for entitlement in entitlements:
        entitlement.expired_at = datetime.now()
        try:
          entitlement.save()
        except:
          log.error("Unable to cancel entitlement id %s" % (entitlement.id))
          pass

  # Cancels a subscriptions
  # Deletes a Stripe subscription and record in Transactions
  def cancel_subscription(self, subscription):

    try:
      if subscription.user is not None:
        stripe.Subscription.delete(subscription.stripe_subscription_id)
        
      self._cancel_enrollments_entitlements(subscription)
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

  # Set all enrollments to sub. plan courses to is_active=true
  # Set all entitlements to sub. plan courses to expire date to None
  # Record renewal transaction
  def _renew_enrollments_entitlements(self, subscription):
    plan_course_ids = subscription.subscription_plan.bundle.courses.values('id')
    plan_course_uuids = list(map(lambda id: get_course_uuid_for_course(str(id)), plan_course_ids))
    
    if subscription.user is not None:
      # Public user case
      enrollments = CourseEnrollment.objects.filter(user_id=subscription.user.id, course_id__in=plan_course_ids)
      entitlements = CourseEntitlement.objects.filter(user_id=subscription.user.id, course_uuid__in=plan_course_uuids) 
    
    elif subscription.enterprise is not None:
      # enterprise case
      enterprise_user_ids = EnterpriseCustomerUser.objects.filter(enterprise_customer_id=subscription.enterprise.uuid).values('user_id')
      enrollments = CourseEnrollment.objects.filter(user_id__in=enterprise_user_ids, course_id__in=plan_course_ids)
      entitlements = CourseEntitlement.objects.filter(user_id__in=enterprise_user_ids, course_uuid__in=plan_course_uuids)
    
    else:
      raise Exception("Subscription should have user or enterprise field values.")

    for enrollment in enrollments:
        enrollment.is_active = True
        try:
          enrollment.save()
        except:
          log.error("Unable to renew enrollment id %s" % (enrollment.id))
          pass

    for entitlement in entitlements:
        entitlement.expired_at = None
        try:
          entitlement.save()
        except:
          log.error("Unable to renew entitlement id %s" % (entitlement.id))
          pass

    self.record_transaction(subscription, SubscriptionTransaction.RENEW.value)
  
  

  # Creates a new Stripe Subscription if the current one can be renewed
  # Then renew enrollments and entitlements
  def renew_subscription(self, subscription):

    valid_subscription_plan = subscription.subcription_plan.valid_until > datetime.now() & subscription.subcription_plan.is_active
    if valid_subscription_plan:
      raise Exception("Cannot renew subscription. Subscription Plan might be no longer active or expired.")
    if subscription.status is not Statuses.CANCELLED.value: 
      raise Exception("Cannot renew subscription. Must be in CANCELLED state")
    if subscription.stripe_customer_id is None: 
      raise Exception("Cannot renew subscription. Missing Stripe Customer ID of Subscription ID %s", (subscription.id))
    
    try:
      
      sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
      if sub.status is not 'cancelled':
        raise Exception("Cannot renew subscription. Stripe Subscription %s is not yet cancelled. ", (subscription.stripe_subscription_id))
    
      new_subscription = self.create_subscription(subscription, subscription.stripe_customer_id)
      
      subscription.stripe_subscription_id = new_subscription.get('stripe_subscription_id')
      stripe_invoice_id = new_subscription.get('stripe_invoice_id')
      subscription.status = Statuses.ACTIVE.value
      subscription.save()
      self._renew_enrollments_entitlements(subscription)
      self.record_transaction(subscription, SubscriptionTransaction.RENEW.value, stripe_invoice_id)

    except Exception as e:
      log.error(str(e))
      raise

  # Proactively check Stripe Subscriptions cancelled status and make necessary actions
  # Should be run in a cronjob
  def check_stripe_subscription_cancelled_status(self, subscription):
    sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
    if sub.status is 'cancelled' and subscription.status is not Statuses.CANCELLED.value:
      self.cancel_subscription(subscription)

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

    