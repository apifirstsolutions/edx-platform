import logging
from bridgekeeper import perms
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework.mixins import (
    CreateModelMixin, 
    ListModelMixin, 
    RetrieveModelMixin, 
    UpdateModelMixin
)
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.viewsets import GenericViewSet
from rest_framework.authentication import SessionAuthentication

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from openedx.core.djangoapps.content.course_overviews.serializers import CourseOverviewBaseSerializer
from openedx.core.lib.api.authentication import BearerAuthentication

from ..services.subscription import SubscriptionService
from ..models import Bundle, Statuses, SubscriptionPlan, Subscription, SubscriptionTransaction
from ..serializers import (
  SubscriptionPlanSerializer,
  SubscriptionSerializer, 
)
from ..permissions import (
  VIEW_SUBSCRIPTION_PLAN, 
)

AUTHENTICATION_CLASSES = (JwtAuthentication, BearerAuthentication, SessionAuthentication,)

log = logging.getLogger(__name__)
subscription_svc = SubscriptionService()
User = get_user_model()
class SubscriptionPlanViewSet(
  GenericViewSet,
  RetrieveModelMixin,
  ListModelMixin):

  serializer_class = SubscriptionPlanSerializer
  authentication_classes = AUTHENTICATION_CLASSES

  def get_queryset(self):
      """
      Returns all subscription plans
      """

      plans = SubscriptionPlan.objects.all()
      return perms[VIEW_SUBSCRIPTION_PLAN].filter(self.request.user, plans).order_by('order')
class FeaturedSubscriptionPlan(ListAPIView):
    serializer_class = SubscriptionPlanSerializer

    def get_queryset(self):
      """
      Returns all featured subscription plan
      """
    
      plans = SubscriptionPlan.objects.filter(is_featured=True)
      return perms[VIEW_SUBSCRIPTION_PLAN].filter(self.request.user, plans).order_by('order')

class PlanCourses(ListAPIView):
    serializer_class = CourseOverviewBaseSerializer
    
    def get_queryset(self):
      """
      Returns all Courses bundled in a Plan
      """
      plan_id = self.kwargs['id']
      
      try:
        plan = SubscriptionPlan.objects.get(id=plan_id)
        return plan.bundle.courses.all()
      
      except (SubscriptionPlan.DoesNotExist, Exception):
        return []
      
class SubscriptionViewSet(
  GenericViewSet,
  CreateModelMixin,
  RetrieveModelMixin,
  UpdateModelMixin,
  ListModelMixin):

  serializer_class = SubscriptionSerializer
  authentication_classes = AUTHENTICATION_CLASSES
  http_method_names = ['get', 'post', 'patch']
  queryset = Subscription.objects.all()

  def _cancel_subscription(subscription, new_status):
    if subscription.user is not None and \
      subscription.status in [ Statuses.ACTIVE.value, Statuses.INACTIVE.value ] and \
      new_status in [ Statuses.CANCELLED.value, Statuses.EXPIRED.value ]:
      return subscription_svc.cancel_subscription(subscription)


  def create(self, request):
    # {
    #   "billing_cycle": "month",
    #   "license_count": 1,
    #   "subscription_plan_slug": "slug",
    #   "user": 15,
    #   "status": "active"
    #   "ecommerce_order_number": "string',
    #   "stripe_customer_id": "string'
    # }

    result = { 'id': None }
    
    try:
      user = User.objects.get(id=request.data.get('user'))
      plan = SubscriptionPlan.objects.get(slug=request.data.get('subscription_plan_slug'))
      subscription =  Subscription.objects.create(
        billing_cycle=request.data.get('billing_cycle'),
        license_count=1,
        subscription_plan=plan,
        user=user,
        status='active',
      )

      sub_extra = subscription_svc.create_subscription(subscription, request.data.get('stripe_customer_id'))
      subscription.stripe_customer_id = sub_extra.get('stripe_customer_id')
      subscription.stripe_subscription_id = sub_extra.get('stripe_subscription_id')
      subscription.stripe_price_id = sub_extra.get('stripe_price_id')
      stripe_invoice_id = sub_extra.get('stripe_invoice_id')
      subscription.save()
      subscription_svc.record_transaction(subscription, SubscriptionTransaction.CREATE.value, stripe_invoice_id, request.data.get('ecommerce_order_number'))
      
      result['id'] = subscription.id

    except Exception as e:
      raise

    return JsonResponse(result)
    
  def update(self, request, pk=None):
    """
    Disabled. Go to Django Admin to edit Subscriptions
    """
    pass

  def partial_update(self, request, pk=None):
    """
    Use only to Cancel or Expire an active, non-enterprise Subscriptions.
    """

    try:
      subscription = Subscription.objects.get(id=pk)

      if subscription is not None and request.data['status'] is not None:
        new_status = request.data['status']

        if subscription.user is not None and \
          subscription.status in [ Statuses.ACTIVE.value, Statuses.INACTIVE.value ] and \
          new_status in [ Statuses.CANCELLED.value, Statuses.EXPIRED.value ]:

          result = subscription_svc.cancel_subscription(subscription)
          
          if not result['success']:
            return JsonResponse(result)
          else:
            subscription.status = new_status
            subscription.save()
            return JsonResponse(result)
      else:
        return Response(
          { 'message': "Use only to Cancel or Expire an active, non-enterprise Subscriptions." }, 
          status=HTTP_400_BAD_REQUEST
        )
    except Exception as e:
      log.error("Error in cancelling/expiring user subscription.")
      raise

