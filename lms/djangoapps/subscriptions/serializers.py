from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from rest_framework.serializers import ModelSerializer
from openedx.core.djangoapps.content.course_overviews.serializers import (
    CourseOverviewBaseSerializer,
)
from .models import Bundle, SubscriptionPlan, Subscription
class BundleSerializer(ModelSerializer):
  courses = CourseOverviewBaseSerializer(many=True, read_only=True) 
  class Meta:
    model = Bundle
    fields = '__all__'
class SubscriptionPlanSerializer(ModelSerializer):
  # bundle = BundleSerializer()
  class Meta:
    model = SubscriptionPlan
    fields = '__all__'

class SubscriptionSerializer(ModelSerializer):
  class Meta:
    model = Subscription
    fields = '__all__'