from django.conf.urls import include, re_path
from rest_framework.routers import DefaultRouter
from ..views import api

router = DefaultRouter()
router.register('plan', api.SubscriptionPlanViewSet, basename='subscriptions')
router.register('subscription', api.SubscriptionViewSet, basename='subscriptions')

urlpatterns = [
    re_path('^', include(router.urls)),
    re_path(r'^featured-plans', api.FeaturedSubscriptionPlan.as_view()),
    re_path(r'^plan/(?P<id>\w+)/courses', api.PlanCourses.as_view()),
]