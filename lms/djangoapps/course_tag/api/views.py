"""
API views for CourseTag
"""

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
from .serializers import CourseTagSerializer
class LazyPageNumberPagination(NamespacedPageNumberPagination):
    """
    NamespacedPageNumberPagination that works with a LazySequence queryset.

    The paginator cache uses ``@cached_property`` to cache the property values for
    count and num_pages.  It assumes these won't change, but in the case of a
    LazySquence, its count gets updated as we move through it.  This class clears
    the cached property values before reporting results so they will be recalculated.

    """

    def get_paginated_response(self, data):
        # Clear the cached property values to recalculate the estimated count from the LazySequence
        del self.page.paginator.__dict__['count']
        del self.page.paginator.__dict__['num_pages']

        # Paginate queryset function is using cached number of pages and sometime after
        # deleting from cache when we recalculate number of pages are different and it raises
        # EmptyPage error while accessing the previous page link. So we are catching that exception
        # and raising 404. For more detail checkout PROD-1222
        page_number = self.request.query_params.get(self.page_query_param, 1)
        try:
            self.page.paginator.validate_number(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=str(exc)
            )
            self.page.number = self.page.paginator.num_pages
            raise NotFound(msg)

        return super(LazyPageNumberPagination, self).get_paginated_response(data)


@view_auth_classes(is_authenticated=True)
class CourseTagApi(DeveloperErrorViewMixin, ListAPIView):

    class CourseTagPageNumberPagination(LazyPageNumberPagination):
        max_page_size = 100

    pagination_class = CourseTagPageNumberPagination
    serializer_class = CourseTagSerializer
    authentication_classes = (
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
        JwtAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        course_tag = CourseTag.objects.filter(course_tag_type__platform__in = ['BOTH', 'MOBILE']).order_by("course_tag_type")
        return LazySequence(
        (c for c in course_tag ),
        est_len=course_tag.count()
        )
