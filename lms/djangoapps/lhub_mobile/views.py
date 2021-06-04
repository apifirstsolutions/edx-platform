from django.shortcuts import render
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework import permissions
from .models import MobileUserSessionCookie
from openedx.core.lib.api.mixins import PutAsCreateMixin
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from openedx.core.lib.api.authentication import BearerAuthentication
from rest_framework.authentication import SessionAuthentication
from .permissions import ApiKeyOrModelPermission
from .serializers import CourseSerializer
from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.commerce.api.v1.models import Course
from django.http import Http404


class UserSessionCookieView(ViewSet):
    """
        **Use Cases**

            Get  a user's session cookie for mobile apps webview.

        **Example Request**

            GET /api/lhub_mobile/getSessionCookie/

    """
    authentication_classes = (
        BearerAuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser
    )
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        session_cookies = MobileUserSessionCookie.objects.filter(user=request.user)
        if session_cookies:
            session_cookie_obj = session_cookies.latest('id')
            return Response({'message': "", 'status': True, 'result':{'session_cookie': session_cookie_obj.session_cookie}, 'status_code':200})
        return Response({'message': "Session Cookie Not Found", 'status': True, 'result':{}, 'status_code':400})


class CourseRetrieveUpdateView(PutAsCreateMixin, RetrieveUpdateAPIView):
    """ Retrieve, update, or create courses/modes. """
    lookup_field = 'id'
    lookup_url_kwarg = 'course_id'
    model = CourseMode
    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication,)
    permission_classes = (ApiKeyOrModelPermission,)
    serializer_class = CourseSerializer

    # Django Rest Framework v3 requires that we provide a queryset.
    # Note that we're overriding `get_object()` below to return a `Course`
    # rather than a CourseMode, so this isn't really used.
    queryset = CourseMode.objects.all()

    def get_object(self, queryset=None):
        course_id = self.kwargs.get(self.lookup_url_kwarg)
        course = Course.get(course_id)

        if course:
            return course

        raise Http404

    def pre_save(self, obj):
        # There is nothing to pre-save. The default behavior changes the Course.id attribute from
        # a CourseKey to a string, which is not desired.
        pass

