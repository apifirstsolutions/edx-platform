from lms.envs.common import (
  STRIPE_API_KEY,
  STRIPE_WEBHOOK_SECRET_KEY,
)

class Subscriptions:
  # TODO 
  # After creating a Subscription plan in DB,
  # (1) Create an equivalent ecommerce product with multiple price options.
  # (2) Update Subscription Plan with Ecommerce ID
  # (3) Create a Product and Price in Stripe.
  # (4) Update Subscription Plan with Product and Price ID(s)
  def createPlan(self, plan_id):
    pass

  # TODO - 
  # (1) After first payment create a Stripe subscription with Price (from subscription plan)
  # (2) create a Subscription in DB with ecommerce transaction ID
  def createSubscriptionByEcommerce(self, transaction_id=None):
    pass


  # TODO - 
  # (1) Create a Stripe subscription with Price (from subscription plan)
  # (2) Creating a Subscription in DB,z
  # (1) Update with ecommerce transactionId (optional) for first payment
  def createSubscriptionByAdmin(self, use_biller=False, transaction_id=None):
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



  