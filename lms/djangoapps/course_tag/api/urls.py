"""
URLs for CourseTag API
"""


from django.conf.urls import url

from .views import CourseTagApi


urlpatterns = [
    url('^$', CourseTagApi.as_view(), name='course_tag_api'),

]
