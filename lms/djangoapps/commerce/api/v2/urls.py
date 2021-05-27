"""
Commerce URLs
"""

from django.conf import settings
from django.conf.urls import include, url
from django.urls import path
from . import views

COURSE_URLS = ([
    url(r'^$', views.CourseListView.as_view(), name='list'),\
    # url(r'^$', views.WebCourseListView.as_view()),
], 'courses')

app_name = 'v2'

urlpatterns = [
    url(r'^courses/', include(COURSE_URLS)),
    url(r'^courses/{}'.format(settings.COURSE_KEY_PATTERN), views.CourseDetailView.as_view(), name="course-detail"),
    path('add_product/', views.add_product_to_basket),
    path('add_voucher/', views.add_voucher_to_basket),
    url(r'^checkout/{}'.format(settings.COURSE_KEY_PATTERN), views.CourseCheckoutDetailView.as_view(), name="course-detail-checkout"),
    url(r'^basket-details/$', views.get_basket_content, name='get_basket_detail'),
    url(r'^basket-details/(?P<id>[0-9]+)$', views.get_basket_content, name='get_basket_detail'),
    url(r'^basket_details_mobile/$', views.get_basket_content_mobile, name='get_basket_detail_mobile'),
    url(r'^update_discount/(?P<sku>[\w\-]+)/$', views.update_discount, name='update_discount'),
    url(r'^web/courses/$', views.WebCourseListView.as_view(), name = "web-courses")
]
