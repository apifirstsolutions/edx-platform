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
    fields = [ 'name', 'slug', 'stripe_prod_id', 'ecommerce_prod_id', 'description', 'bundle', 'is_active', 'is_featured', 'valid_until', 
      'price_month', 'stripe_price_month_id', 'price_year', 'stripe_price_year_id', 'price_onetime', 
      'grace_period', 'enterprise',
    ]

class SubscriptionPlanAdmin(admin.ModelAdmin):
  form = SubscriptionPlanForm
  fields = [ 'name', 'slug', 'stripe_prod_id', 'ecommerce_prod_id', 'description', 'bundle', 'is_active', 'is_featured', 'valid_until', 
    'price_month', 'stripe_price_month_id', 'price_year', 'stripe_price_year_id', 'price_onetime', 
    'grace_period', 'enterprise',
  ]
  readonly_fields = ['slug', 'ecommerce_prod_id', 'stripe_prod_id', 'stripe_price_month_id', 'stripe_price_year_id']
  search_fields = ['name', 'description', 'enterprise__name']
  list_display = ['slug', 'name', 'description', 'enterprise', 'is_featured', 'stripe_prod_id']

  def save_model(self, request, obj, form, change):
    subscription_svc = SubscriptionService()

    if not change:
      # On create
      prices = { 
        'month': obj.price_month, 
        'year': obj.price_year,
      }
      product = subscription_svc.create_product(obj.name, prices)
      if product is not None:
        obj.stripe_prod_id = product['stripe_product_id']
        obj.stripe_price_month_id = product['stripe_price_month_id']
        obj.stripe_price_year_id = product['stripe_price_year_id']

    else:
      # On update

      new_product_name = None
      if 'name' in form.changed_data:
        new_product_name = obj.name

      # If month/year prices change, need to create new prices in stripe 
      # https://stripe.com/docs/billing/subscriptions/products-and-prices#changing-prices
      new_prices = {
        'month': None, 
        'year': None,
      }

      if 'price_month' in form.changed_data:
        new_prices['month'] = obj.price_month

      if 'price_year' in form.changed_data:
        new_prices['year'] = obj.price_year
  
      updated_product = subscription_svc.update_product(new_product_name, new_prices, obj.stripe_prod_id)
      
      if updated_product is not None:
        if updated_product['stripe_price_month_id'] is not None:
          obj.stripe_price_month_id = updated_product['stripe_price_month_id']
        if updated_product['stripe_price_year_id'] is not None:
          obj.stripe_price_year_id = updated_product['stripe_price_year_id']

    super().save_model(request, obj, form, change)

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)