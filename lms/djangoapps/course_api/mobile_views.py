"""
Course API Views
"""


from django.core.exceptions import ValidationError
from django.core.paginator import InvalidPage
from edx_rest_framework_extensions.paginators import NamespacedPageNumberPagination
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import NotFound
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from openedx.core.lib.api.authentication import BearerAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.serializers import ValidationError
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes

from . import USE_RATE_LIMIT_2_FOR_COURSE_LIST_API, USE_RATE_LIMIT_10_FOR_COURSE_LIST_API
from .mobile_api import list_courses
from .forms import CourseDetailGetForm, CourseIdListGetForm, CourseListGetForm
from .mobile_serializers import CourseDetailSerializer, CourseKeySerializer, CourseSerializer, CategorySerializer, SubCategorySerializer
#from openedx/core/djangoapps/content import Category, SubCategory
from openedx.core.djangoapps.content.course_overviews.models import Category, SubCategory, CourseOverview
from openedx.core.lib.api.view_utils import LazySequence
import importlib
custom_reg_form = importlib.import_module('lms.djangoapps.custom-form-app', 'custom_reg_form')
from custom_reg_form.models import UserExtraInfo
from django.db.models import Count, F, Q
#from itertools import chain
#from django.forms.models import model_to_dict
#from django.db.models import F
from student.models import CourseEnrollment
from lms.djangoapps.courseware.courses import get_courses_with_extra_info_json
from rest_framework.decorators import api_view
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication
import six

import logging
log = logging.getLogger(__name__) 

@view_auth_classes(is_authenticated=False)
class CourseDetailView(DeveloperErrorViewMixin, RetrieveAPIView):
    """
    **Use Cases**

        Request details for a course

    **Example Requests**

        GET /api/courses/v1/courses/{course_key}/

    **Response Values**

        Body consists of the following fields:

        * effort: A textual description of the weekly hours of effort expected
            in the course.
        * end: Date the course ends, in ISO 8601 notation
        * enrollment_end: Date enrollment ends, in ISO 8601 notation
        * enrollment_start: Date enrollment begins, in ISO 8601 notation
        * id: A unique identifier of the course; a serialized representation
            of the opaque key identifying the course.
        * media: An object that contains named media items.  Included here:
            * course_image: An image to show for the course.  Represented
              as an object with the following fields:
                * uri: The location of the image
        * name: Name of the course
        * number: Catalog number of the course
        * org: Name of the organization that owns the course
        * overview: A possibly verbose HTML textual description of the course.
            Note: this field is only included in the Course Detail view, not
            the Course List view.
        * short_description: A textual description of the course
        * start: Date the course begins, in ISO 8601 notation
        * start_display: Readably formatted start of the course
        * start_type: Hint describing how `start_display` is set. One of:
            * `"string"`: manually set by the course author
            * `"timestamp"`: generated from the `start` timestamp
            * `"empty"`: no start date is specified
        * pacing: Course pacing. Possible values: instructor, self

        Deprecated fields:

        * blocks_url: Used to fetch the course blocks
        * course_id: Course key (use 'id' instead)

    **Parameters:**

        username (optional):
            The username of the specified user for whom the course data
            is being accessed. The username is not only required if the API is
            requested by an Anonymous user.

    **Returns**

        * 200 on success with above fields.
        * 400 if an invalid parameter was sent or the username was not provided
          for an authenticated request.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the course is not available or cannot be seen.

        Example response:

            {
                "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Fexample%2F2012_Fall",
                "media": {
                    "course_image": {
                        "uri": "/c4x/edX/example/asset/just_a_test.jpg",
                        "name": "Course Image"
                    }
                },
                "description": "An example course.",
                "end": "2015-09-19T18:00:00Z",
                "enrollment_end": "2015-07-15T00:00:00Z",
                "enrollment_start": "2015-06-15T00:00:00Z",
                "course_id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "overview: "<p>A verbose description of the course.</p>"
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp",
                "pacing": "instructor"
            }
    """

    serializer_class = CourseDetailSerializer

    def get_object(self):
        """
        Return the requested course object, if the user has appropriate
        permissions.
        """
        requested_params = self.request.query_params.copy()
        requested_params.update({'course_key': self.kwargs['course_key_string']})
        form = CourseDetailGetForm(requested_params, initial={'requesting_user': self.request.user})
        if not form.is_valid():
            raise ValidationError(form.errors)

        return course_detail(
            self.request,
            form.cleaned_data['username'],
            form.cleaned_data['course_key'],
        )


class CourseListUserThrottle(UserRateThrottle):
    """Limit the number of requests users can make to the course list API."""
    # The course list endpoint is likely being inefficient with how it's querying
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

        return super(CourseListUserThrottle, self).allow_request(request, view)



class PopularCourseListUserThrottle(UserRateThrottle):
    """Limit the number of requests users can make to the course list API."""
    # The course list endpoint is likely being inefficient with how it's querying
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

        return super(PopularCourseListUserThrottle, self).allow_request(request, view)




class CategoryListUserThrottle(UserRateThrottle):
    """Limit the number of requests users can make to the course list API."""
    # The course list endpoint is likely being inefficient with how it's querying
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

        return super(CategoryListUserThrottle, self).allow_request(request, view)






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

#@view_auth_classes(is_authenticated=True)
class CourseListView(DeveloperErrorViewMixin, ListAPIView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsAuthenticated,)

    class CourseListPageNumberPagination(LazyPageNumberPagination):
        max_page_size = 100

    pagination_class = CourseListPageNumberPagination
    serializer_class = CourseSerializer
    throttle_classes = (CourseListUserThrottle,)

    def get_queryset(self):
        """
        Yield courses visible to the user.
        """
        form = CourseListGetForm(self.request.query_params, initial={'requesting_user': self.request.user})
        if not form.is_valid():
            raise ValidationError(form.errors)
        user_extra_info = UserExtraInfo.objects.filter(user_id=self.request.user.id).first()
        if hasattr(user_extra_info, 'industry_id'):
            user_category = Category.objects.filter(id=user_extra_info.industry_id).first()
            if form.cleaned_data['filter_'] is not None:
                form.cleaned_data['filter_'].update({'new_category':user_category.name})
            else:
                form.cleaned_data['filter_'] = {'new_category':user_category.id}
        result= list_courses(
            self.request,
            form.cleaned_data['username'],
            org=form.cleaned_data['org'],
            platform='Mobile',
            filter_=form.cleaned_data['filter_'],
            search_term=form.cleaned_data['search_term'],
            get_extra_info=True
        )
        return result



@view_auth_classes(is_authenticated=False)
class PopularCourseListView(DeveloperErrorViewMixin, ListAPIView):
    class PopularCourseListPageNumberPagination(LazyPageNumberPagination):
        max_page_size = 100

    pagination_class = PopularCourseListPageNumberPagination
    serializer_class = CourseSerializer
    throttle_classes = (PopularCourseListUserThrottle,)

    def get_queryset(self):
        """
        Yield courses visible to the user.
        """
        form = CourseListGetForm(self.request.query_params, initial={'requesting_user': self.request.user})
        if not form.is_valid():
            raise ValidationError(form.errors)
        courses = CourseOverview.objects.all().values('course_id')
        log.info('====== enrollments =========')
        #queryset=CourseEnrollment.objects.filter(is_active=True).values('course_id').order_by().annotate(Count('course_id')).values('course_id__count','course_id').annotate(enrollment_count=F('course_id__count')).values('course_id','enrollment_count')
        queryset=CourseEnrollment.objects.filter(Q(is_active=True) & Q(course_id__in=courses)).values('course_id').order_by().annotate(Count('course_id')).filter(course_id__count__gte=3).values('course_id__count','course_id').annotate(enrollment_count=F('course_id__count')).values('course_id','enrollment_count')
        log.info(queryset)
        user_extra_info = UserExtraInfo.objects.filter(user_id=self.request.user.id).first()
        if hasattr(user_extra_info, 'industry_id'):
            user_category = Category.objects.filter(id=user_extra_info.industry_id).first()
            if form.cleaned_data['filter_'] is not None:
                form.cleaned_data['filter_'].update({'category':user_category.name})
            else:
                form.cleaned_data['filter_'] = {'category':user_category.name}
        result= list_courses(
            self.request,
            form.cleaned_data['username'],
            org=form.cleaned_data['org'],
            filter_=form.cleaned_data['filter_'],
            search_term=form.cleaned_data['search_term']
        )
        return result




@view_auth_classes(is_authenticated=True)
class CategoryListView(DeveloperErrorViewMixin, ListAPIView):

    class CategoryListPageNumberPagination(LazyPageNumberPagination):
        max_page_size = 100

    pagination_class = CategoryListPageNumberPagination
    serializer_class = CategorySerializer
    throttle_classes = (CourseListUserThrottle,)

    def get_queryset(self):
        platform_visibility = self.request.query_params.get('platform_visibility', None)
        form = CourseListGetForm(self.request.query_params, initial={'requesting_user': self.request.user})
        if not form.is_valid():
            raise ValidationError(form.errors)
        if platform_visibility:
            categories_count = CourseOverview.objects.filter( Q(platform_visibility=platform_visibility) | Q(platform_visibility='both'), new_category__isnull=False).values('new_category','id').order_by().annotate(Count('new_category')).values('new_category__count','new_category').annotate(course_count=F('new_category__count'),category=F('new_category')).values('category','course_count')
        else:
            categories_count = CourseOverview.objects.filter(platform_visibility='both' , new_category__isnull=False).values('new_category','id').order_by().annotate(Count('new_category')).values('new_category__count','new_category').annotate(course_count=F('new_category__count'),category=F('new_category')).values('category','course_count')    
        categories = []
        for cat in categories_count:
            if Category.objects.filter(id=cat['category']).exists():
                cat_id = Category.objects.filter(id=cat['category']).values()[0]
                cat['category'] =  cat_id['name']
                cat['category_image'] = cat_id['category_image']
                cat['id'] = cat_id['id']
                categories.append(cat)
        return LazySequence(
        (c for c in categories),
        est_len=len(categories)
        )

class CustomAPIException(ValidationError):
    """
    raises API exceptions with custom messages and custom status codes
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'error'

    def __init__(self, detail, status_code=None):
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code

@view_auth_classes(is_authenticated=True)
class SubCategoryListView(DeveloperErrorViewMixin, ListAPIView):

    class SubCategoryListPageNumberPagination(LazyPageNumberPagination):
        max_page_size = 100

    pagination_class = SubCategoryListPageNumberPagination
    serializer_class = SubCategorySerializer
    authentication_classes = (JwtAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self, *args, **kwargs):
        category = self.request.GET.get('category',None)
        qs = None
        if category:
            if category.isnumeric():
                qs = SubCategory.objects.filter(category=category)
                return qs
            else:
                raise CustomAPIException("Invalid course ID.", status_code=status.HTTP_404_NOT_FOUND)
        else:
            return SubCategory.objects.all()


class CourseIdListUserThrottle(UserRateThrottle):
    """Limit the number of requests users can make to the course list id API."""

    THROTTLE_RATES = {
        'user': '20/minute',
        'staff': '40/minute',
    }

    def allow_request(self, request, view):
        # Use a special scope for staff to allow for a separate throttle rate
        user = request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            self.scope = 'staff'
            self.rate = self.get_rate()
            self.num_requests, self.duration = self.parse_rate(self.rate)

        return super(CourseIdListUserThrottle, self).allow_request(request, view)


@view_auth_classes()
class CourseIdListView(DeveloperErrorViewMixin, ListAPIView):
    """
    **Use Cases**

        Request a list of course IDs for all courses the specified user can
        access based on the provided parameters.

    **Example Requests**

        GET /api/courses/v1/courses_ids/

    **Response Values**

        Body comprises a list of course ids and pagination details.

    **Parameters**

        username (optional):
            The username of the specified user whose visible courses we
            want to see.

        role (required):
            Course ids are filtered such that only those for which the
            user has the specified role are returned. Role can be "staff"
            or "instructor".
            Case-insensitive.

    **Returns**

        * 200 on success, with a list of course ids and pagination details
        * 400 if an invalid parameter was sent or the username was not provided
          for an authenticated request.
        * 403 if a user who does not have permission to masquerade as
          another user who specifies a username other than their own.
        * 404 if the specified user does not exist, or the requesting user does
          not have permission to view their courses.

        Example response:

            {
                "results":
                    [
                        "course-v1:edX+DemoX+Demo_Course"
                    ],
                "pagination": {
                    "previous": null,
                    "num_pages": 1,
                    "next": null,
                    "count": 1
                }
            }

    """
    class CourseIdListPageNumberPagination(LazyPageNumberPagination):
        max_page_size = 1000

    pagination_class = CourseIdListPageNumberPagination
    serializer_class = CourseKeySerializer
    throttle_classes = (CourseIdListUserThrottle,)

    def get_queryset(self):
        """
        Returns CourseKeys for courses which the user has the provided role.
        """
        form = CourseIdListGetForm(self.request.query_params, initial={'requesting_user': self.request.user})
        if not form.is_valid():
            raise ValidationError(form.errors)

        return list_course_keys(
            self.request,
            form.cleaned_data['username'],
            role=form.cleaned_data['role'],
        )


@api_view()
@authentication_classes((BearerAuthentication,SessionAuthentication,))
@permission_classes([IsAuthenticated])
def get_recommended_courses_for_web(request,id=None):

    filter_ = {}
    user_extra_info = UserExtraInfo.objects.filter(user_id=request.user.id).first()
    if hasattr(user_extra_info, 'industry_id'):
        user_category = Category.objects.filter(id=user_extra_info.industry_id).first()
        filter_.update({'new_category':user_category.id})

    courses = get_courses_with_extra_info_json(request.user, platform='Web', filter_=filter_)
    course_list = []
    for course in courses:
        if course.advertised_start:
            course_start = course.advertised_start.strftime("%b") + " " + str(course.advertised_start.day) +", " + str(course.advertised_start.year)
        else:
            course_start = course.start.strftime("%b") + " " + str(course.start.day) + ", " + str(course.start.year)
        course_dict = {'id': six.text_type(course.id), 'org':course.display_org_with_default, 'name': course.display_name, 'image': course.course_image_url
        ,'code':course.display_number_with_default,'difficulty_level': course.difficulty_level, 'enrollments_count': course.enrollments_count\
        ,'ratings': course.ratings, 'comments_count': course.comments_count, 'price': course.price, 'discount_applicable': course.discount_applicable\
        , 'discounted_price': course.discounted_price, 'discount_percentage':course.discount_percentage, 'start': course_start, 'discount_type':course.discount_type\
        , 'available_vouchers': course.available_vouchers}
        course_list.append(course_dict)
        
    return Response({'result':course_list})
