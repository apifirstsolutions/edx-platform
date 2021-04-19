"""
Commerce URLs
"""


from django.conf import settings
from django.conf.urls import include, url

from ..views import EnrollmentListViewMobile

COURSE_URLS = ([
    url(r'^$', EnrollmentListViewMobile.as_view(), name='list'),
], 'enrollments')

app_name = 'v2'

urlpatterns = [
    url(r'^v2/enrollment/', include(COURSE_URLS)),
]
