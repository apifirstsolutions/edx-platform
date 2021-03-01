"""
Course API URLs
"""


from django.conf import settings
from django.conf.urls import include, url

from .views import CourseDetailView, CourseIdListView, CourseListView
from .mobile_views import CategoryListView , PopularCourseListView, SubCategoryListView, CourseListView as MobileCourseListView, get_recommended_courses_for_web

urlpatterns = [
    url(r'^v1/courses/$', CourseListView.as_view(), name="course-list"),
    url(r'^v2/web_recommended/courses/$',get_recommended_courses_for_web, name="course-list"),
    url(r'^v2/recommended/courses/$', MobileCourseListView.as_view(), name="course-list"),
    url(r'^v2/courses/categories/$', CategoryListView.as_view(), name="category-list"),
    url(r'^v2/courses/subcategories/$', SubCategoryListView.as_view(), name="subcategory-list"),
    url(r'^v2/popular/courses/$', PopularCourseListView.as_view(), name="course-list"),
    url(r'^v1/courses/{}'.format(settings.COURSE_KEY_PATTERN), CourseDetailView.as_view(), name="course-detail"),
    url(r'^v1/course_ids/$', CourseIdListView.as_view(), name="course-id-list"),
    url(r'', include('course_api.blocks.urls'))
]
