from django.http import HttpResponse
from django.shortcuts import render

from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
)
from rest_framework.viewsets import GenericViewSet

from ..models import Bundle, SubscriptionPlan, Subscription, License
from ..serializers import BundleSerializer, SubscriptionPlanSerializer, SubscriptionSerializer, LicenseSerializer

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

class SubscriptionViewSet(
  GenericViewSet,  # generic view functionality
  CreateModelMixin,  # handles POSTs
  RetrieveModelMixin,  # handles GETs for 1 Company
  UpdateModelMixin,  # handles PUTs and PATCHes
  ListModelMixin):  # handles GETs for many Companies

  serializer_class = SubscriptionSerializer
  queryset = Subscription.objects.all()

class LicenseViewSet(
  GenericViewSet,  # generic view functionality
  CreateModelMixin,  # handles POSTs
  RetrieveModelMixin,  # handles GETs for 1 Company
  UpdateModelMixin,  # handles PUTs and PATCHes
  ListModelMixin):  # handles GETs for many Companies

  serializer_class = LicenseSerializer
  queryset = License.objects.all()

