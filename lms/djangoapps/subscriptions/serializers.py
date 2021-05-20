from rest_framework.serializers import ModelSerializer

from .models import Bundle, SubscriptionPlan, Subscription, License, Statuses, BillingCycles
from .helpers.enum_field import EnumField
# from enumfields.drf.fields import EnumField

class BundleSerializer(ModelSerializer):
  class Meta:
    model = Bundle
    # course =  TODO 
    fields = (
      'id', 'name', 'slug', 'description', 'enterprise_id', 'created_at', 'updated_at',
    )

class SubscriptionPlanSerializer(ModelSerializer):
  class Meta:
    model = SubscriptionPlan
    fields = (
      'id', 'name', 'bundle_id', 'ecommerce_prod_id', 'description', 'is_active', 'valid_until', 
      'monthly_price', 'yearly_price', 'one_time_price', 'grace_period', 'enterprise_id', 'created_at', 'updated_at',
    )

class SubscriptionSerializer(ModelSerializer):
  class Meta:
    model = Subscription
    # status = EnumField(enum=Statuses) # TODO - add status 
    # billing_cycle = EnumField(enum=BillingCycles) # TODO - add billing_cycle 
    fields = (
      'id', 'subscription_plan', 'user_id', 'enterprise_id','start_at', 'end_at', 
      'biller_subscription_id', 'ecommerce_trans_id','license_count', 'created_at', 'updated_at',
    )

class LicenseSerializer(ModelSerializer):
  class Meta:
    model = License
    # status = EnumField(enum=Statuses)     # TODO - add status 
    fields = (
      'id', 'subscription', 'user', 'created_at', 'updated_at',
    )