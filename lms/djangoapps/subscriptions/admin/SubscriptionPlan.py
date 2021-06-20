import logging
from ckeditor.widgets import CKEditorWidget
from django import forms
from django.contrib import admin
from ..models import SubscriptionPlan
from ..services.subscription import SubscriptionService
  
logger = logging.getLogger(__name__)

class SubscriptionPlanForm(forms.ModelForm):
  description = forms.CharField(widget = CKEditorWidget())
  class Meta:
    model = SubscriptionPlan
    fields = [ 'name', 'slug', 'stripe_prod_id', 'ecommerce_prod_id', 'description', 'image_url', 'bundle', 
      'is_active', 'is_featured', 'is_utap_supported', 'valid_until', 
      'price_month', 'stripe_price_id_month', 'price_year', 'stripe_price_id_year', 'price_onetime', 
      'order', 'enterprise',
    ]

class SubscriptionPlanAdmin(admin.ModelAdmin):
  form = SubscriptionPlanForm
  fields = [ 'name', 'slug', 'stripe_prod_id', 'ecommerce_prod_id', 'description', 'image_url', 'bundle', 
    'is_active', 'is_featured', 'is_utap_supported', 'valid_until', 
    'price_month', 'stripe_price_id_month', 'price_year', 'stripe_price_id_year', 'price_onetime', 
    'order', 'enterprise',
  ]
  readonly_fields = ['slug', 'ecommerce_prod_id', 'stripe_prod_id', 'stripe_price_id_month', 'stripe_price_id_year']
  search_fields = ['name', 'description', 'enterprise__name']
  list_display = ['slug', 'name', 'description', 'enterprise', 'is_featured', 'order', 'stripe_prod_id']

  def save_model(self, request, plan, form, change):
    subscription_svc = SubscriptionService()

    if not change:
      # On Create - create Stripe and Ecommerce products with prices.
      prices = { 
        'month': plan.price_month, 
        'year': plan.price_year,
        'onetime': plan.price_onetime,
      }
      
      try:
        product_data = subscription_svc.create_product(plan, prices, user=request.user)
      except Exception as e:
        logger.error(u"Error creating Subscription as product. %s", str(e))
        raise
      
      plan.stripe_prod_id = product_data.get('stripe_product_id')
      plan.stripe_price_id_month = product_data.get('stripe_price_id_month')
      plan.stripe_price_id_year = product_data.get('stripe_price_id_year')

      plan.ecommerce_prod_id = product_data.get('ecommerce_prod_id')
      plan.ecommerce_prod_id_month = product_data.get('ecommerce_prod_id_month')
      plan.ecommerce_prod_id_year = product_data.get('ecommerce_prod_id_year')
      plan.ecommerce_prod_id_onetime = product_data.get('ecommerce_prod_id_onetime')

      plan.ecommerce_stockrecord_id_month = product_data.get('ecommerce_stockrecord_id_month')
      plan.ecommerce_stockrecord_id_year = product_data.get('ecommerce_stockrecord_id_year')
      plan.ecommerce_stockrecord_id_onetime = product_data.get('ecommerce_stockrecord_id_onetime')
        
    else:
      # On update
      new_product_name = None
      new_description = None
      new_valid_until = None
      
      if 'name' in form.changed_data:
        new_product_name = plan.name
      if 'description' in form.changed_data:
        new_description = plan.description
      if 'valid_until' in form.changed_data:
        new_valid_until = plan.valid_until

      # If month/year prices change, create new prices in stripe 
      # https://stripe.com/docs/billing/subscriptions/products-and-prices#changing-prices
      new_prices = {
        'month': None, 
        'year': None,
        'onetime': None,
      }

      if 'price_month' in form.changed_data:
        new_prices['month'] = plan.price_month

      if 'price_year' in form.changed_data:
        new_prices['year'] = plan.price_year

      try:
        updated_product = subscription_svc.update_product(
          user=request.user,
          plan=plan,
          new_prices=new_prices,
          new_product_name=new_product_name,
          new_description=new_description,
          new_valid_until=new_valid_until,
        )
      except Exception as e:
        logger.error(u"Error updating Subscription product. %s", str(e))
        raise
      
      if updated_product is not None:
        plan.stripe_price_id_month = updated_product.get('stripe_price_id_month')
        plan.stripe_price_id_year = updated_product.get('stripe_price_id_year')
          
    super().save_model(request, plan, form, change)

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)