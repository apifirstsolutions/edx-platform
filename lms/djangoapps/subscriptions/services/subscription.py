
import logging
import stripe
from itertools import islice

from ..models import BillingCycles, License, Transactions, SubscriptionTransaction
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
          # cancel_at=<valid_until>  # TODO - should cancel when valid_until change
        )

        result['stripe_customer_id'] = stripe_customer_id
        result['stripe_subscription_id'] = sub.id
        result['stripe_invoice_id'] = sub.latest_invoice
        
      except Exception as e:
        log.error(u"Error occured creating Subscription in Stripe. %s", str(e))
        raise

      
    # TODO assign_course_entitlement_to_user in LMS

    return result
  
  
  def create_single_license(self, subscription, stripe_invoice_id=None):
    License.objects.create(user=subscription.user, subscription=subscription)
    # FIXME - handle update case. Add ecommerce trans id
    self.record_transaction(subscription, SubscriptionTransaction.CREATE.value, stripe_invoice_id=stripe_invoice_id)
    

  def create_enterprise_licenses(self, subscription):
    BATCH_SIZE = 1000
    
    # https://docs.djangoproject.com/en/3.0/ref/models/querysets/#bulk-create
    licenses = ( License(subscription=subscription) for i in range(subscription.license_count) )

    while True:
      batch = list(islice(licenses, BATCH_SIZE))
      if not batch:
        break
      License.objects.bulk_create(batch, BATCH_SIZE)
      self.record_transaction(subscription, SubscriptionTransaction.CREATE.value)
    
  
  # Cancels a subscriptions
  # Deletes a Stripe subscription and record in Transactions
  def cancel_subscription(self, subscription):

    try:
      stripe.Subscription.delete(subscription.stripe_subscription_id)
      self.record_transaction(subscription, SubscriptionTransaction.CANCEL.value)
      return { 'success': True }
    except Exception as e:
      log.error(u"Error occured cancelling Subscription in Stripe. %s", str(e))
      raise

    

  # Update a Subscription cancel time
  def update_subscription_validity():
    # cancel_at=<valid_until>  # TODO - should cancel when Subscription Plan valid_until date change 
    pass

  # TODO - 
  # (1) After firstpayment is detected from webhook, update the current subscription and next billing date
  # (2) On expiration, update subscription status and subs. history
  # (3) On cancellation, update subscription status and subs. history
  # (2) Create a Stripe subscription with Price (from subscription plan)
  def renewSubscription(self, next_billing_date):
    pass


  

  # TODO - 
  # Check Stripe Subscriptions status for payments and transaction information (like invoices)
  # make necessary subscription status updates
  def checkSubscription(self, subscription_id):
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


  # after suscbscription user is entitled to all courses in the bundle assoc. with the Subscription Plan
  def assign_course_entitlements():
    pass
    


  