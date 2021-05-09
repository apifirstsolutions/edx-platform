from django.conf.urls import include, re_path
from rest_framework.routers import DefaultRouter
from ..views.api import BundleViewSet, SubscriptionPlanViewSet

router = DefaultRouter()
router.register('bundle', BundleViewSet, basename='subscriptions')
router.register('plan', SubscriptionPlanViewSet, basename='subscriptions')

urlpatterns = [
    re_path('^', include(router.urls))
]