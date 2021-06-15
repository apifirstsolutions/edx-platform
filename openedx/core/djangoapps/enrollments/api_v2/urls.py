"""
Commerce URLs
"""


from django.conf import settings
from django.conf.urls import include, url
from django.urls import path

from ..views import EnrollmentListViewMobile, ProgressDataViewMobile, SearchCourseEnrollmentListViewMobile

COURSE_URLS = ([
    url(r'^$', EnrollmentListViewMobile.as_view(), name='list'),
], 'enrollments')

app_name = 'v2'

urlpatterns = [
    url(r'^v2/enrollment/', include(COURSE_URLS)),
    url(r'^v2/progressdata/', ProgressDataViewMobile.as_view(), name='progress'),
    path('v2/search_course_enrollment/', SearchCourseEnrollmentListViewMobile.as_view(),
         name='search_course_enrollment'),
]
