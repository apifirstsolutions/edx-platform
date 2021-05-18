from django.conf.urls import url
from lms.djangoapps.lhub_extended_api import views

urlpatterns = [
    url(r'^orders$', views.LHUBOrdersHistoryView.as_view()),
    url(r'^orders/(?P<order_number>[-\w]+)$', views.LHUBOrderDetailView.as_view()),
]
