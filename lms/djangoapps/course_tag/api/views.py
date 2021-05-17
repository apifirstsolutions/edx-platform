"""
API views for CourseTag
"""
from collections import OrderedDict

from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import APIException, NotFound
from openedx.core.lib.api.view_utils import LazySequence
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from edx_rest_framework_extensions.paginators import NamespacedPageNumberPagination
from django.core.paginator import InvalidPage
from rest_framework.permissions import IsAuthenticated
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from lms.djangoapps.course_tag.models import CourseTag, CourseTagType
from .serializers import CourseTagTypeSerializer
from rest_framework import pagination
from rest_framework.response import Response

from logging import getLogger
logger = getLogger(__name__)
#
class LazyPageNumberPagination(pagination.PageNumberPagination):
    """
    NamespacedPageNumberPagination that works with a LazySequence queryset.

    The paginator cache uses ``@cached_property`` to cache the property values for
    count and num_pages.  It assumes these won't change, but in the case of a
    LazySquence, its count gets updated as we move through it.  This class clears
    the cached property values before reporting results so they will be recalculated.

    """
    page_size = 10
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):

        return Response({
            'message': "",
            'result': {'results': data},
            'pagination' : {'next': self.get_next_link(),'previous': self.get_previous_link(), 'count':self.page.paginator.count, 'num_pages': self.page.paginator.num_pages},
            'status': True,
            'status_code':200
        })

@view_auth_classes(is_authenticated=True)
class CourseTagTypeApi(DeveloperErrorViewMixin, ListAPIView):

    class CourseTagTypePageNumberPagination(LazyPageNumberPagination):
        max_page_size = 100

    pagination_class = CourseTagTypePageNumberPagination
    serializer_class = CourseTagTypeSerializer
    authentication_classes = (
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
        JwtAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        course_tag_type = CourseTagType.objects.filter(is_enabled=True, platform__in=['BOTH', 'MOBILE']).distinct()
        if course_tag_type:
            return LazySequence(
                (c for c in course_tag_type),
                est_len=course_tag_type.count()
            )

