import stripe
from itertools import islice

from .models import License, Transactions

from lms.envs.common import (
  STRIPE_API_KEY,
  STRIPE_CURRENCY,
)

stripe.api_key = STRIPE_API_KEY
class SubscriptionService:
  
  # Creates a Product and Prices in Stripe.
  # Creates an Ecommerce Product with multiple prices options.
  def create_product(self, name, prices):
    try:
      product = stripe.Product.create(name=name,)
      result = {}
      result['stripe_product_id'] = product.id

      print("DEBUGGGGG:")
      print(prices)
      print(prices.keys())

      # keys must be interval values in stripe https://stripe.com/docs/api/prices/object#price_object-recurring-interval
      for interval in prices.keys():
        if prices[interval] is not None:
          price = stripe.Price.create(
            unit_amount= prices[interval] * 100,
            currency=STRIPE_CURRENCY,
            recurring={ 'interval': interval },
            product=product.id,
          )

          result['stripe_price_' + interval + '_id'] = price.id
      
      # TODO - create Ecommerce Product and Prices

      return result
    except Exception as e:
      print('Stripe ERROR:: ' + str(e))

  
  # Updates a Produc name and Prices in Stripe.
  # Updates an Ecommerce Product with multiple prices options.
  def update_product(self, new_product_name, new_prices, stripe_product_id):
    try:
      result = {}
      
      if new_product_name is not None:
        stripe.Product.modify(stripe_product_id, name=new_product_name)

      for interval in new_prices.keys():
        if new_prices[interval] is not None:
          price = stripe.Price.create(
            unit_amount= int(new_prices[interval] * 100),
            currency=STRIPE_CURRENCY,
            recurring={ 'interval': interval },
            product=stripe_product_id,
          )

          result['stripe_price_' + interval + '_id'] = price.id
      
      # TODO - update Ecommerce Product and Prices

      return result
    
    except Exception as e:
      print('Stripe ERROR:: ' + str(e))


  # If using Stripe - after first payment, create a Stripe subscription with Price (from subscription plan)
  def create_subscription(self, user, price_id, billing_cycle_anchor, one_time_pay=False, first_payment_transaction_id=None):
    result = {
      'stripe_customer_id': None,
      'stripe_subscription_id': None,
      'stripe_invoice_id': None,
    }
    
    if not one_time_pay:
      try:
        customer_id = 'cus_JYiGFvd6zlyJHr'  # FIXME must be taken from ecommerce records. if does not exists, where to store when creating?
        sub = stripe.Subscription.create(
          customer=customer_id,
          billing_cycle_anchor=billing_cycle_anchor,
          proration_behavior='none',
          items=[
            { "price": price_id },
          ],
        )

        result['stripe_customer_id'] = customer_id
        result['stripe_subscription_id'] = sub.id
        result['stripe_invoice_id'] = sub.latest_invoice
        
      except Exception as e:
        print('Stripe ERROR:: ' + str(e))

    return result
  
  
  def create_single_license(self, subscription):
    License.objects.create(user=subscription.user, subscription=subscription)
    

  def create_enterprise_licenses(self, subscription):
    BATCH_SIZE = 1000
    
    # https://docs.djangoproject.com/en/3.0/ref/models/querysets/#bulk-create
    licenses = ( License(subscription=subscription) for i in range(subscription.license_count) )

    while True:
      batch = list(islice(licenses, BATCH_SIZE))
      if not batch:
        break

      print("DEBUG license")
      print(batch)
      License.objects.bulk_create(batch, BATCH_SIZE)
  
  # TODO - 
  # (1) After firstpayment is detected from webhook, update the current subscription and next billing date
  # (2) On expiration, update subscription status and subs. history
  # (3) On cancellation, update subscription status and subs. history
  # (2) Create a Stripe subscription with Price (from subscription plan)
  def renewSubscription(self, next_billing_date):
    pass


  # Cancel a subscriptions
  # set status of subscription to cancelled, and record in subscription history
  def cancelSubscription(self, subscriptio_id):
    pass


  # Expire a subscriptions
  # set status of subscription to expired, , and record in subscription history
  def expireSubscription(self, subscription_id):
    pass


  # Check Stripe Subscriptions status for payments and transaction information (like invoices)
  # make necessary subscription status updates
  def checkSubscription(self, subscription_id):
    pass


  # record transations when subscription status changes
  def record_transaction(self, subscription, action, stripe_invoice_id=None, ecommerce_trans_id=None):
    Transactions.objects.create(
      subscription=subscription, 
      status=subscription.status, 
      description=action, 
      license_count=subscription.license_count,
      stripe_invoice_id=stripe_invoice_id,
      ecommerce_trans_id=ecommerce_trans_id,
    )
    


  