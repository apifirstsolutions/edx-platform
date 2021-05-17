import logging
from django import forms
from django.contrib import admin
from lms.djangoapps.courseware.courses import get_courses
from .models import Bundle, License, Subscription, SubscriptionPlan

logger = logging.getLogger(__name__)
class BundleForm(forms.ModelForm):
  description = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))
  class Meta:
    model = Bundle
    fields = ['slug', 'name', 'description', 'enterprise', 'courses']

class BundleAdmin(admin.ModelAdmin):
  form = BundleForm
  filter_horizontal = ('courses',) 
  readonly_fields = ['slug']
  search_fields = ('name', 'description', 'enterprise__name' )
  list_display = ('slug', 'name', 'enterprise')

admin.site.register(Bundle, BundleAdmin)

class CustomModelChoiceField(forms.ModelChoiceField):
  def label_from_instance(self, obj):
    return obj.name
class SubscriptionPlanForm(forms.ModelForm):
  description = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))
  # bundle = CustomModelChoiceField(queryset=Bundle.objects.all()) 
  class Meta:
    model = SubscriptionPlan
    fields = [
      'slug', 'name', 'description', 'bundle', 'is_active', 'valid_until', 
      'billing_cycle_options', 'grace_period', 'enterprise', 'ecommerce_prod_id'
    ]

class SubscriptionPlanAdmin(admin.ModelAdmin):
  form = SubscriptionPlanForm
  readonly_fields = ['slug', 'ecommerce_prod_id']
  search_fields = ('name', 'description', 'enterprise__name' )
  list_display = ('slug', 'name', 'description', 'enterprise')

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)


admin.site.register(Subscription)
admin.site.register(License)

