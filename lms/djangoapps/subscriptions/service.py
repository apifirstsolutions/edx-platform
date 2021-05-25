import stripe

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

  
  # Updates a Product and Prices in Stripe.
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


  # (1) If using Stripe, after first payment create a Stripe subscription with Price (from subscription plan)
  # (2) Create Licenses and Transaction records.
  def createSubscription(self, stripe_customer_id, stripe_price_id, use_stripe=False, first_payment_transaction_id=None):
    if use_stripe:
      try:
        stripe.Subscription.create(
          customer=stripe_customer_id,
          items=[
            { "price": stripe_price_id },
          ],
        )
      except Exception as e:
        print('Stripe ERROR:: ' + str(e))

    else:
      pass # TODO - create licenses and record transaction only. For one-time pay or enterprise use case.
  
  
  
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
  def recordTransaction(self, subscription_id, status, license_count, ecommerce_trans_id=None, biller_invoice_id=None):
    pass



  