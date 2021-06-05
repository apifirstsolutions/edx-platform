from django.conf.urls import include, re_path
from rest_framework.routers import DefaultRouter
from ..views.api import (
    SubscriptionPlanViewSet, 
    FeaturedSubscriptionPlan, 
    SubscriptionViewSet, 
    PlanCourses,
)

router = DefaultRouter()
router.register('plan', SubscriptionPlanViewSet, basename='subscriptions')
router.register('subscription', SubscriptionViewSet, basename='subscriptions')

urlpatterns = [
    re_path('^', include(router.urls)),
    re_path(r'^plan/\?featured', FeaturedSubscriptionPlan.as_view()),
    re_path(r'^plan/(?P<id>\w+)/courses', PlanCourses.as_view()),
]