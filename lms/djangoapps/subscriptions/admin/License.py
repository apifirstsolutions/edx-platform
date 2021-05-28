import logging
from django import forms
from django.contrib import admin
from ..models import License

logger = logging.getLogger(__name__)

class LicenseAdmin(admin.ModelAdmin):
  fields = [ 'subscription', 'user']

  def get_plan_name(self, obj):
    return obj.subscription.subscription_plan.name
    
  get_plan_name.short_description = 'Subscription Plan'
  get_plan_name.admin_order_field = 'subscription__subscription_plan__name'

  def get_enterprise_name(self, obj):
    if obj.subscription.enterprise is not None:
      return obj.subscription.enterprise.name
    
  get_enterprise_name.short_description = 'Enterprise'
  get_enterprise_name.admin_order_field = 'subscription__enterprise__name'

  def get_status(self, obj):
    return obj.subscription.status
    
  get_status.short_description = 'Status'
  get_status.admin_order_field = 'subscription__status'


  def get_user_name(self, obj):
    if obj.user is not None:
      return obj.user.username
    
  get_user_name.short_description = 'User'
  get_user_name.admin_order_field = 'user__username'


  search_fields = ['subscription__subscription_plan__name', 'user__username', 'subscription__enterprise__name']
  list_display = ['get_plan_name', 'get_user_name', 'get_enterprise_name', 'get_status']

admin.site.register(License, LicenseAdmin)