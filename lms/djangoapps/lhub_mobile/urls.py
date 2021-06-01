from django.urls import path
from django.conf.urls import include, url
from django.conf import settings
from .views import UserSessionCookieView, CourseRetrieveUpdateView


GETVIEW = UserSessionCookieView.as_view({
    'get': 'get',
})


COURSE_URLS = ([
    url(r'^{}/$'.format(settings.COURSE_ID_PATTERN), CourseRetrieveUpdateView.as_view(), name='retrieve_update'),
], 'courses')

urlpatterns = [
#    path('', views.index, name='index'),
    url(
        r'^getSessionCookie/$',
        GETVIEW,
        name='get_user_cookie_api'
    ),
    url(r'^courses/', include(COURSE_URLS)),
]
