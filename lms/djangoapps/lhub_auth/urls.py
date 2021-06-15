from django.conf.urls import include, re_path
from rest_framework.routers import DefaultRouter
from .views import (
    ScidCustomerView, 
    # MyInfoViewSet,
)

# router = DefaultRouter()
# TODO - Create these views for SCID Proxy
# router.register('customer', ScidCustomerView.as_view(), basename='scid')
# router.register('myinfo', MyInfoViewSet, basename='scid')

urlpatterns = [
    # re_path('^', include(router.urls)),
    # url(r'^$', ScidCustomerView.as_view(), basename='scid'),
    re_path(r'^customer/(?P<id>\w+)$', ScidCustomerView.as_view(), name='scid'),
]