from rest_framework.serializers import ModelSerializer, ListSerializer
from openedx.core.djangoapps.content.course_overviews.serializers import (
    CourseOverviewBaseSerializer,
)
from .models import Bundle, SubscriptionPlan, Subscription, License

class BundleSerializer(ModelSerializer):
  courses = ListSerializer(child=CourseOverviewBaseSerializer()) 
  class Meta:
    model = Bundle
    fields = (
      'id', 'name', 'slug', 'description', 'courses', 'enterprise_id', 'created_at', 'updated_at',
    )

class SubscriptionPlanSerializer(ModelSerializer):
  bundle = BundleSerializer()
  class Meta:
    model = SubscriptionPlan
    fields = (
      'id', 'name', 'slug', 'bundle', 'ecommerce_prod_id', 'description', 'is_active', 'is_featured', 'valid_until', 
      'price_month', 'price_year', 'price_onetime', 'grace_period', 'enterprise_id', 'created_at', 'updated_at',
    )

class SubscriptionSerializer(ModelSerializer):
  class Meta:
    model = Subscription
    # status = EnumField(enum=Statuses) # TODO - add status 
    # billing_cycle = EnumField(enum=BillingCycles) # TODO - add billing_cycle 
    fields = (
      'id', 'subscription_plan', 'billing_cycle', 'user_id', 'enterprise_id','start_at', 'end_at', 
      'stripe_subscription_id', 'stripe_customer_id', 'stripe_price_id', 'license_count', 'created_at', 'updated_at',
    )

class LicenseSerializer(ModelSerializer):
  class Meta:
    model = License
    # status = EnumField(enum=Statuses)     # TODO - add status 
    fields = (
      'id', 'subscription', 'user', 'created_at', 'updated_at',
    )