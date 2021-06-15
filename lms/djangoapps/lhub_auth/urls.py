from django.conf.urls import include, re_path
from rest_framework.routers import DefaultRouter
from .views import (
    ScidCustomerViewSet, 
    MyInfoViewSet,
)

router = DefaultRouter()
# TODO - Create these views for SCID Proxy
# router.register('customer', ScidCustomerViewSet, basename='scid')
# router.register('myinfo', MyInfoViewSet, basename='scid')

urlpatterns = [
    re_path('^', include(router.urls)),
]