import logging
import datetime
from django import forms
from django.contrib import admin
from ..models import Subscription, License, BillingCycles, SubscriptionTransaction
from ..service import SubscriptionService

logger = logging.getLogger(__name__)
class SubscriptionForm(forms.ModelForm):
  class Meta:
    model = Subscription
    fields = [ 'subscription_plan', 'billing_cycle', 'user', 'enterprise', 'start_at', 'status', 
      'license_count', 'stripe_subscription_id', 'stripe_customer_id', 'stripe_price_id']
class SubscriptionAdmin(admin.ModelAdmin):
  form = SubscriptionForm

  fields = [ 'subscription_plan', 'billing_cycle', 'user', 'enterprise', 'start_at', 'status', 
    'license_count', 'stripe_subscription_id', 'stripe_customer_id', 'stripe_price_id']
  readonly_fields = ['stripe_subscription_id', 'stripe_customer_id', 'stripe_price_id']
  search_fields = ['subscription_plan__name', 'billing_cycle', 'user__email', 'enterprise__name']
  list_display = ['subscription_plan', 'billing_cycle', 'user', 'enterprise']

  

  def save_model(self, request, obj, form, change):
    subscription_svc = SubscriptionService()
  
    stripe_invoice_id = None

    if not change and obj.status == 'active':   # TODO - throw error when status is not ACTIVE durinng creation
      
      # determine strip_price_id based from billing_cycle selection
      if obj.billing_cycle == 'month' or obj.billing_cycle == 'year':
        obj.stripe_price_id = getattr(obj.subscription_plan, 'stripe_price_'+obj.billing_cycle+'_id')

      # If start_at is not set, set to first day of the next month, exept current day is already first day of the month
      if obj.start_at is None:
        today = datetime.datetime.today()
        if today.day == 1:
          billing_cycle_anchor = int(today.timestamp())
        else:
          # https://stackoverflow.com/questions/57353919/how-can-i-get-the-first-day-of-the-next-month-in-python
          nextmonth_first_day = (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
          billing_cycle_anchor = int(nextmonth_first_day.timestamp())
      else:
        billing_cycle_anchor = int(obj.start_at.timestamp()) + 20   # add 20sec to ensure future time for billing_cycle_anchor else Stripe will thrown an error
        
      if obj.billing_cycle is not 'one-time' and obj.user is not None:
        sub = subscription_svc.create_subscription(obj.user, obj.stripe_price_id, billing_cycle_anchor)

        if sub is not None:
          obj.stripe_customer_id = sub['stripe_customer_id']
          obj.stripe_subscription_id = sub['stripe_subscription_id']
          stripe_invoice_id = sub['stripe_invoice_id']

      else:
        # Enterprise subscription
        subscription_svc.create_subscription(obj.enterprise, price_id=None, billing_cycle_anchor=None, one_time_pay=True)

    # updating case
    else:
      pass

    
    super().save_model(request, obj, form, change)
    
    if (obj.user is not None):
      subscription_svc.create_single_license(obj)
    if (obj.enterprise is not None):
      subscription_svc.create_enterprise_licenses(obj)

    # FIXME - handle update case. Add ecommerce trans id
    subscription_svc.record_transaction(obj, 'CREATED', stripe_invoice_id=stripe_invoice_id, ecommerce_trans_id=None)



admin.site.register(Subscription, SubscriptionAdmin)