
import datetime

# Determine Subscription billing_cycle_anchor 
# https://stripe.com/docs/api/subscriptions/object#subscription_object-billing_cycle_anchor
def get_billing_cycle_anchor(start_at=None):
    # If start_at is not set, it will be set to current datetime
    if start_at is None:
        today = datetime.datetime.today()
        billing_cycle_anchor = int(today.timestamp()) + 1800
    else:
        # adding 30min here to ensure it will be future date to avoid stripe error. 
        billing_cycle_anchor = int(start_at.timestamp()) + 1800

    return billing_cycle_anchor