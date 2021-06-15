"""
Course API Views
"""


from django.core.exceptions import ValidationError
from django.core.paginator import InvalidPage
from edx_rest_framework_extensions.paginators import NamespacedPageNumberPagination
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated  
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes

from lms.djangoapps.course_api import USE_RATE_LIMIT_2_FOR_COURSE_LIST_API, USE_RATE_LIMIT_10_FOR_COURSE_LIST_API
from lms.djangoapps.course_api.mobile_api import list_courses
from lms.djangoapps.course_api.forms import CourseDetailGetForm, CourseIdListGetForm, CourseListGetForm
from .mobile_serializers import ReviewSerializer
#from .serializers import CourseReviewSerializer
#from openedx/core/djangoapps/content import Category, SubCategory
#from openedx.core.djangoapps.content.course_overviews.models import Category, SubCategory
from .models import CourseReview 
from openedx.core.lib.api.view_utils import LazySequence
import importlib
from lms.djangoapps.custom_form_app.custom_reg_form.models import UserExtraInfo
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from opaque_keys.edx.keys import CourseKey


import logging
log = logging.getLogger(__name__) 

class ReviewListUserThrottle(UserRateThrottle):
    """Limit the number of requests users can make to the course review list API."""
    # The course review list endpoint is likely being inefficient with how it's querying
    # various parts of the code and can take courseware down, it needs to be rate
    # limited until optimized. LEARNER-5527

    THROTTLE_RATES = {
        'user': '20/minute',
        'staff': '40/minute',
    }

    def check_for_switches(self):
        if USE_RATE_LIMIT_2_FOR_COURSE_LIST_API.is_enabled():
            self.THROTTLE_RATES = {
                'user': '2/minute',
                'staff': '10/minute',
            }
        elif USE_RATE_LIMIT_10_FOR_COURSE_LIST_API.is_enabled():
            self.THROTTLE_RATES = {
                'user': '10/minute',
                'staff': '20/minute',
            }

    def allow_request(self, request, view):
        self.check_for_switches()
        # Use a special scope for staff to allow for a separate throttle rate
        user = request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            self.scope = 'staff'
            self.rate = self.get_rate()
            self.num_requests, self.duration = self.parse_rate(self.rate)

        return super(ReviewListUserThrottle, self).allow_request(request, view)


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
class ReviewListView(DeveloperErrorViewMixin, ListAPIView):

    """
    **Use Cases**

        Request information on all courses visible to the specified user.

    **Example Requests**

        GET /api/course_reviews/v2/courses/<COURSE_ID>

    **Response Values**

        Body comprises a list of objects as returned by `ReviewListView`.

    **Parameters**

        search_term (optional):
            Search term to filter courses (used by ElasticSearch).

        username (optional):
            The username of the specified user whose visible courses we
            want to see. The username is not required only if the API is
            requested by an Anonymous user.

        org (optional):
            If specified, visible `CourseOverview` objects are filtered
            such that only those belonging to the organization with the
            provided org code (e.g., "HarvardX") are returned.
            Case-insensitive.

    **Returns**

        * 200 on success, with a list of course discovery objects as returned
          by `CourseDetailView`.
        * 400 if an invalid parameter was sent or the username was not provided
          for an authenticated request.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the specified user does not exist, or the requesting user does
          not have permission to view their courses.

    """
    class ReviewListPageNumberPagination(LazyPageNumberPagination):
        max_page_size = 100

    pagination_class = ReviewListPageNumberPagination
    serializer_class = ReviewSerializer
    throttle_classes = (ReviewListUserThrottle,)

    def get_queryset(self):
        """
        Yield courses visible to the user.
        """
        log.info("=====course_review=====")
        course_id = self.kwargs['course_key_string']
        course_key = CourseKey.from_string(course_id)
        course_reviews = CourseOverview.get_from_id(course_key).course_reviews.all()
        # course_reviews = CourseReview.objects.all()
        return LazySequence(
        (c for c in course_reviews ),
        est_len=course_reviews.count()
        )
