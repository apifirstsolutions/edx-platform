"""
URLs for CourseTag API
"""


from django.conf.urls import url

from .views import  CourseTagTypeApi, CourseListViewTag
from lms.djangoapps.course_tag.api import views

urlpatterns = [
    url('^type$', CourseTagTypeApi.as_view(), name='course_tag_api'),
    url('^courses$', views.get_courses_by_course_tag, name='course_tag_courses'),

]
