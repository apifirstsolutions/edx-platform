import logging
from django import forms
from django.contrib import admin
from ..models import SubscriptionPlan
from ..service import SubscriptionService

logger = logging.getLogger(__name__)

class SubscriptionPlanForm(forms.ModelForm):
  description = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))

  class Meta:
    model = SubscriptionPlan
    fields = [
      'name', 'slug', 'description', 'bundle', 'is_active', 'is_featured', 'valid_until', 
      'price_month', 'price_year', 'price_onetime', 'grace_period', 'enterprise', 'ecommerce_prod_id', 'stripe_prod_id'
    ]

class SubscriptionPlanAdmin(admin.ModelAdmin):
  form = SubscriptionPlanForm
  fields = [ 'name', 'slug', 'description', 'bundle', 'is_active', 'is_featured', 'valid_until', 
    'price_month', 'price_year', 'price_onetime', 'grace_period', 'enterprise', 'ecommerce_prod_id', 'stripe_prod_id',
  ]
  readonly_fields = ['slug', 'ecommerce_prod_id', 'stripe_prod_id']
  search_fields = ['name', 'description', 'enterprise__name']
  list_display = ['slug', 'name', 'description', 'enterprise', 'is_featured', 'stripe_prod_id']

  def save_model(self, request, obj, form, change):
    stripe_svc = SubscriptionService()

    if not change:
      # keys must be interval values in stripe https://stripe.com/docs/api/prices/object#price_object-recurring-interval
      prices = { 'month': obj.price_month, 'year': obj.price_year,}
      stripe_data = stripe_svc.create_plan(obj.name, prices)
      if stripe_data is not None:
        obj.stripe_prod_id = stripe_data['product_id']
        obj.stripe_price_month_id = stripe_data['price_month_id']
        obj.stripe_price_year_id = stripe_data['price_year_id']
    else:
      # FIXME Update Plan and prices
      pass
      
    
    # TODOs  Create Ecommerce Product
    
    super().save_model(request, obj, form, change)


admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)