import logging
from django import forms
from django.contrib import admin
from .models import Bundle, License, Subscription, SubscriptionPlan
from .service import SubscriptionService

logger = logging.getLogger(__name__)
class BundleForm(forms.ModelForm):
  description = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))
  class Meta:
    model = Bundle
    fields = ['slug', 'name', 'description', 'enterprise', 'courses']

class BundleAdmin(admin.ModelAdmin):
  form = BundleForm
  filter_horizontal = ['courses']
  readonly_fields = ['slug']
  search_fields = ['name', 'description', 'enterprise__name']
  list_display = ['slug', 'name', 'enterprise']
class SubscriptionPlanForm(forms.ModelForm):
  description = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))

  class Meta:
    model = SubscriptionPlan
    fields = [
      'slug', 'name', 'description', 'bundle', 'is_active', 'is_featured', 'valid_until', 
      'monthly_price', 'yearly_price', 'one_time_price', 'grace_period', 'enterprise', 'ecommerce_prod_id', 'stripe_prod_id'
    ]

  

class SubscriptionPlanAdmin(admin.ModelAdmin):
  form = SubscriptionPlanForm
  readonly_fields = ['slug', 'ecommerce_prod_id', 'stripe_prod_id']
  search_fields = ['name', 'description', 'enterprise__name']
  list_display = ['slug', 'name', 'description', 'enterprise', 'is_featured', 'stripe_prod_id']

  def save_model(self, request, obj, form, change):
    if not change:
      prices = {
        "month": obj.monthly_price,
        "year": obj.yearly_price,
        "one-time": obj.one_time_price
      }
      stripe_svc = SubscriptionService()
      stripe_data = stripe_svc.create_plan(obj.name, prices)
      obj.stripe_prod_id = stripe_data['product_id']
    
    super().save_model(request, obj, form, change)


admin.site.register(Bundle, BundleAdmin)
admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(Subscription)
admin.site.register(License)

