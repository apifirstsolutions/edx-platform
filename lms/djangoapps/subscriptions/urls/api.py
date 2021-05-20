from django.conf.urls import include, re_path
from rest_framework.routers import DefaultRouter
from ..views.api import BundleViewSet, SubscriptionPlanViewSet, FeaturedSubscriptionPlan, SubscriptionViewSet, LicenseViewSet

router = DefaultRouter()
router.register('bundle', BundleViewSet, basename='subscriptions')
router.register('plan', SubscriptionPlanViewSet, basename='subscriptions')
router.register('subscription', SubscriptionViewSet, basename='subscriptions')
router.register('license', LicenseViewSet, basename='subscriptions')

urlpatterns = [
    re_path('^', include(router.urls)),
    re_path('^featured-plans', FeaturedSubscriptionPlan.as_view()),
]