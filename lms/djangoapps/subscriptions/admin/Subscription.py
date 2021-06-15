import logging
from django import forms
from django.contrib import admin

from ..models import Subscription, BillingCycles, SubscriptionTransaction, Statuses
from ..services.subscription import SubscriptionService
from ..helpers import stripe_utils

logger = logging.getLogger(__name__)
subscription_svc = SubscriptionService()
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
    if obj.user is not None and obj.enterprise is not None:
      raise Exception('User and Enterprise cannot have values at the same time.')

    stripe_invoice_id = None
    action = None
   
    if not change:
      # On create
      action = SubscriptionTransaction.CREATE.value
      
      if obj.status in [ Statuses.CANCELLED.value, Statuses.EXPIRED.value]:
        raise Exception('Subscription status cannot be CANCELLED or EXPIRED on creation.')
      
      try:
        subscription = subscription_svc.create_subscription(obj)
        obj.stripe_customer_id = subscription.get('stripe_customer_id')
        obj.stripe_subscription_id = subscription.get('stripe_subscription_id')
        obj.stripe_price_id = subscription.get('stripe_price_id')
        stripe_invoice_id = subscription.get('stripe_invoice_id')
      
      except Exception as e:
        raise

    else:
      # On Update
      if 'status' in form.changed_data and obj.status in [ Statuses.CANCELLED.value, Statuses.EXPIRED.value ]:
        if obj.status == Statuses.CANCELLED.value:
          action = SubscriptionTransaction.CANCEL.value
        if obj.status == Statuses.EXPIRED.value:
          action = SubscriptionTransaction.EXPIRE.value
        subscription_svc.cancel_subscription(obj)

    super().save_model(request, obj, form, change)
    subscription_svc.record_transaction(obj, action, stripe_invoice_id)

    # Set Licenses
    # FIXME can be merged into single method

    if not change:
      if (obj.user is not None):
        subscription_svc.create_single_license(obj, stripe_invoice_id=stripe_invoice_id)
      if (obj.enterprise is not None):
        subscription_svc.create_enterprise_licenses(obj)

    else:
      # TODO handle increase/decrease of License Count
      pass


admin.site.register(Subscription, SubscriptionAdmin)