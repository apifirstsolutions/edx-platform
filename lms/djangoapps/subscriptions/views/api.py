from django.http import JsonResponse
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
)
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import ListAPIView
from rest_framework.serializers import ListSerializer
from ..models import Statuses, Subscription
from ..service import SubscriptionService

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from ..models import Bundle, SubscriptionPlan, Subscription, License
from ..serializers import (
  BundleSerializer, 
  SubscriptionPlanSerializer,
  SubscriptionSerializer, 
)

from openedx.core.djangoapps.content.course_overviews.serializers import (
    CourseOverviewBaseSerializer,
)
class BundleViewSet(
  GenericViewSet,  # generic view functionality
  CreateModelMixin,  # handles POSTs
  RetrieveModelMixin,  # handles GETs for 1 object
  UpdateModelMixin,  # handles PUTs and PATCHes
  ListModelMixin):  # handles GETs for many object

  serializer_class = BundleSerializer
  queryset = Bundle.objects.all()

class SubscriptionPlanViewSet(
  GenericViewSet,
  RetrieveModelMixin,
  ListModelMixin):

  serializer_class = SubscriptionPlanSerializer
  queryset = SubscriptionPlan.objects.all()
class FeaturedSubscriptionPlan(ListAPIView):
    serializer_class = SubscriptionPlanSerializer

    def get_queryset(self):
      """
      Returns all featured subscription plan
      """
      return SubscriptionPlan.objects.filter(is_featured=True, is_active=True)

class PlanCourses(ListAPIView):
    serializer_class = CourseOverviewBaseSerializer
    
    def get_queryset(self):
      """
      Returns all Courses bundled in a Plan
      """
      plan_id = self.kwargs['id']
      plan = SubscriptionPlan.objects.get(id=plan_id)
      return plan.bundle.courses.all()
class SubscriptionViewSet(
  GenericViewSet,
  CreateModelMixin,
  RetrieveModelMixin,
  UpdateModelMixin,
  ListModelMixin):

  serializer_class = SubscriptionSerializer
  queryset = Subscription.objects.all()

  def partial_update(self, request, pk=None):
    subscription = Subscription.objects.get(id=pk)
    new_status = request.data['status']
    
    if subscription.user is not None and \
      subscription.status in [ Statuses.ACTIVE.value, Statuses.INACTIVE.value ] and \
      new_status in [ Statuses.CANCELLED.value, Statuses.EXPIRED.value ]:

      svc = SubscriptionService()
      result = svc.cancel_subscription(subscription)
      
      if not result['success']:
        return JsonResponse(result)
      else:
        subscription.status = new_status
        subscription.save()
        return JsonResponse(result)

