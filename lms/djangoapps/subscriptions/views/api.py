from django.http import HttpResponse
from django.shortcuts import render

from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
)
from rest_framework.viewsets import GenericViewSet

from ..models import Bundle, SubscriptionPlan, Subscription
from ..serializers import BundleSerializer, SubscriptionPlanSerializer

class BundleViewSet(
  GenericViewSet,  # generic view functionality
  CreateModelMixin,  # handles POSTs
  RetrieveModelMixin,  # handles GETs for 1 Company
  UpdateModelMixin,  # handles PUTs and PATCHes
  ListModelMixin):  # handles GETs for many Companies

  serializer_class = BundleSerializer
  queryset = Bundle.objects.all()


class SubscriptionPlanViewSet(
  GenericViewSet,  # generic view functionality
  CreateModelMixin,  # handles POSTs
  RetrieveModelMixin,  # handles GETs for 1 Company
  UpdateModelMixin,  # handles PUTs and PATCHes
  ListModelMixin):  # handles GETs for many Companies

  serializer_class = SubscriptionPlanSerializer
  queryset = SubscriptionPlan.objects.all()


def BundleUIViewdetail(request, bundle_id):
    return HttpResponse("Bundle %s." % bundle_id)
