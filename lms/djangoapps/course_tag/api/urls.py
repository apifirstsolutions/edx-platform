"""
URLs for CourseTag API
"""


from django.conf.urls import url

from .views import  CourseTagTypeApi


urlpatterns = [
    url('^type$', CourseTagTypeApi.as_view(), name='course_tag_api'),
]
