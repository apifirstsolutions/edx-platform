from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
)
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import ListAPIView

from ..models import Bundle, SubscriptionPlan, Subscription, License
from ..serializers import BundleSerializer, SubscriptionPlanSerializer, SubscriptionSerializer, LicenseSerializer

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
  CreateModelMixin,
  RetrieveModelMixin,
  UpdateModelMixin,
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

class SubscriptionViewSet(
  GenericViewSet,
  CreateModelMixin,
  RetrieveModelMixin,
  UpdateModelMixin,
  ListModelMixin):

  serializer_class = SubscriptionSerializer
  queryset = Subscription.objects.all()

class LicenseViewSet(
  GenericViewSet,
  CreateModelMixin,
  RetrieveModelMixin,
  UpdateModelMixin,
  ListModelMixin):

  serializer_class = LicenseSerializer
  queryset = License.objects.all()

