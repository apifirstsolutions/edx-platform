import logging
from django import forms
from django.contrib import admin
from ..models import Subscription

logger = logging.getLogger(__name__)


class SubscriptionForm(forms.ModelForm):
  class Meta:
    model = Subscription
    fields = [ 'subscription_plan', 'billing_cycle', 'user', 'enterprise', 'start_at', 'end_at', 'status', 
      'license_count', 'stripe_subscription_id', 'stripe_customer_id', 'stripe_price_id']
class SubscriptionAdmin(admin.ModelAdmin):
  form = SubscriptionForm
  fields = [ 'subscription_plan', 'billing_cycle', 'user', 'enterprise', 'start_at', 'end_at', 'status', 
    'license_count', 'stripe_subscription_id', 'stripe_customer_id', 'stripe_price_id']
  readonly_fields = ['stripe_subscription_id', 'stripe_customer_id', 'stripe_price_id']
  search_fields = ['subscription_plan__name', 'billing_cycle', 'user__email', 'enterprise__name']
  list_display = ['subscription_plan__name', 'billing_cycle', 'user__email', 'enterprise__name']

admin.site.register(Subscription)