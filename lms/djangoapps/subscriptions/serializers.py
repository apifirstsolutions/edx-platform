from rest_framework.serializers import ModelSerializer

from .models import Bundle,  SubscriptionPlan, Subscription, License

class BundleSerializer(ModelSerializer):
  class Meta:
    model = Bundle
    fields = (
      'id', 'name', 'course_metadata', 'product_id', 'description', 'created_at', 'updated_at',
    )

class SubscriptionPlanSerializer(ModelSerializer):
  class Meta:
    model = SubscriptionPlan
    fields = (
      'id', 'name', 'bundle_id', 'product_id', 'description', 'is_active', 'valid_until', 
      'billing_cycle_options', 'grace_period', 'created_at', 'updated_at',
    )

class SubscriptionSerializer(ModelSerializer):
  class Meta:
    model = Subscription
    fields = (
      'id', 'customer_id', 'is_enterprise', 'subscription_plan', 'billing_cycle', 'start_at', 'end_at', 
      'status', 'license_count', 'created_at', 'updated_at',
    )

class LicenseSerializer(ModelSerializer):
  class Meta:
    model = License
    fields = (
      'id', 'subscription_id', 'user_id', 'created_at', 'updated_at',
    )