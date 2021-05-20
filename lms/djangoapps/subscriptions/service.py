import stripe

from lms.envs.common import (
  STRIPE_API_KEY,
  STRIPE_CURRENCY,
)

stripe.api_key = STRIPE_API_KEY
class SubscriptionService:
  # TODO 
  # After creating a Subscription plan in DB,
  # (1) Create an equivalent ecommerce product with multiple price options.
  # (2) Update Subscription Plan with Ecommerce ID
  # (3) Create a Product and Price in Stripe.
  # (4) Update Subscription Plan with Product and Price ID(s)
  def create_plan(self, name, prices):

    # TODO
    # create stripe product and price
    # use metadata fields to link sub plan to stripe product and priices

    


    # Create Stripe Product and Prices
    try:
      # TODO - try to check if Stripe Product already exists with same plan_slug
      product = stripe.Product.create(
          name=name,
          # metadata={'slug': slug},
          # idempotency_key=       # https://stripe.com/docs/api/idempotent_requests
      )

      for cycle in prices.keys():
        if prices[cycle] is not None and cycle is not 'one-time':   # FIXME handle one-time price
          price = stripe.Price.create(
            unit_amount_decimal= prices[cycle] * 100,
            currency=STRIPE_CURRENCY,
            recurring={ "interval": cycle },
            product=product.id,
          )
      
      return { "product_id": product.id, "price_id": price.id }   # FIXME handle multiple price ids

    except Exception as e:
      print('Stripe ERROR:: ' + str(e))

  # TODO - 
  # (1) After first payment create a Stripe subscription with Price (from subscription plan)
  # (2) create a Subscription in DB with ecommerce transaction ID
  def createSubscriptionByEcommerce(self, stripe_customer_id=None, first_payment_transaction_id=None):
    pass


  # TODO - 
  # (1) Create a Stripe subscription with Price (from subscription plan)
  # (2) Creating a Subscription in DB,z
  # (1) Update with ecommerce transactionId (optional) for first payment
  def createSubscriptionByAdmin(self, use_biller=False, first_payment_transaction_id=None):
    pass

  # TODO - 
  # (1) After firstpayment is detected from webhook, update the current subscription and next billing date
  # (2) On expiration, update subscription status and subs. history
  # (3) On cancellation, update subscription status and subs. history
  # (2) Create a Stripe subscription with Price (from subscription plan)
  def paySubscription(self, next_billing_date):
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



  