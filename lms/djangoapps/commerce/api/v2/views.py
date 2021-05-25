from lms.djangoapps.lhub_ecommerce_offer.models import Coupon
from rest_framework.generics import ListAPIView, RetrieveAPIView
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from openedx.core.lib.api.authentication import BearerAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from .filters import LazyPageNumberPagination
from operator import attrgetter
from ..v1.models import Course, WebCourse
from ..v1.serializers import CourseSerializer, CourseDetailSerializer,CourseDetailCheckoutSerializer,WebCourseSerializer,WebCourseDetailSerializer,WebCourseDetailCheckoutSerializer
import logging
log = logging.getLogger(__name__)
import json
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from opaque_keys.edx.keys import CourseKey
from course_modes.models import CourseMode
from rest_framework.serializers import ValidationError
from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.course_api.blocks.api import get_blocks
from xmodule.modulestore.django import modulestore
from rest_framework.decorators import api_view
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from course_modes.models import CourseMode
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from django.apps import apps
from common.djangoapps.feedback.models import CourseReview

CourseEnrollment = apps.get_model('student', 'CourseEnrollment')

class CourseListView(ListAPIView):
    """ List courses and modes. """
    class CourseListPageNumberPagination(LazyPageNumberPagination):
        max_page_size = 100
    authentication_classes = (JwtAuthentication,BearerAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CourseSerializer
    pagination_class = CourseListPageNumberPagination
    # filter_class = CourseListFilter
    # filterset_class = CourseListFilter
    # filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        filtered_courses = []
        mobile_courses = []
        filter = False
        filters = {'difficulty_level': None, 'sale_type': None, 'subcategory_id': None, 'platform_visibility' : None , 'category' : None, 'discount_applicable': 'Boolean', 'is_premium': 'Boolean'}
        request_filters = {}
        for f,val in filters.items():
            filter_val = self.request.query_params.get(f, None)
            if filter_val is not None:
                filter = True
                if val == 'Boolean':
                    boolean_result = [json.loads(filter_val.split(',')[0].lower())]
                    request_filters[f] = boolean_result
                else:
                    request_filters[f] = filter_val.split(',')

        courses = list(Course.iterator())
        platform_only_courses = []
        for course in courses:
            platform = course.platform_visibility
            if 'platform_visibility' in request_filters.keys():
                request_filters['platform_visibility'].append('both')
                if platform == None or platform in request_filters['platform_visibility']:
                    platform_only_courses.append(course)
            else:
                if platform == None or platform == "both":
                    platform_only_courses.append(course)
        courses = platform_only_courses

        try:
            platform_courses_list = []
            user = self.request.user
            user_org = user.user_extra_info.organization
            authorization = self.request.META.get('HTTP_AUTHORIZATION')

            if "JWT" not in authorization:
                for course in courses:
                    try:
                        course_overview = CourseOverview.get_from_id(course.id)
                        platform = course_overview.platform_visibility
                        organization = course_overview.organization
                        if user.is_staff:
                            platform_courses_list.append(course)
                        elif user_org == organization or organization == None:
                            platform_courses_list.append(course)
                        elif organization == None and user_org == None:
                            platform_courses_list.append(course)
                    except:
                        pass
                courses = platform_courses_list

            else:
                for course in courses:
                    try:
                        course_overview = CourseOverview.get_from_id(course.id)
                        platform = course_overview.platform_visibility
                        organization = course_overview.organization
                        if organization == None:
                            platform_courses_list.append(course)
                    except:
                        pass
                courses = platform_courses_list

        except:
            platform_courses_list = []
            for course in courses:
                try:
                    course_overview = CourseOverview.get_from_id(course.id)
                    platform = course_overview.platform_visibility
                    organization = course_overview.organization
                    if organization == None:
                        platform_courses_list.append(course)
                except:
                    pass
            courses = platform_courses_list

        ordering_filter=self.request.query_params.get('ordering', None)
        if ordering_filter:
            ordering_filter_list = ordering_filter.split(',')
            courses = self.order_courses(courses, ordering_filter_list)
        if filter:
            for course in courses:
                is_filter = [True if getattr(course,f) in val and val is not None else False for f,val in request_filters.items()]
                if all(is_filter):
                    filtered_courses.append(course)
        if self.request.query_params.get('coursename', None):
            filtered_courses_list = []
            course_list = filtered_courses if len(filtered_courses) > 0 else courses
            for course in course_list:
                search_string = self.request.query_params.get('coursename').lower()
                search_string = search_string.strip()
                if course.name.lower().find(search_string) > -1: #and course.platform_visibility in ['mobile', 'both', 'Mobile', 'Both', None]:
                    filtered_courses_list.append(course)

            return filtered_courses_list

        if not self.request.query_params.get('coursename', None) and not filter:
            return courses

        return filtered_courses

    def order_courses(self,course_list, ordering):
        allowed_ordering = ["ratings", "-ratings", "enrollments_count", "-enrollments_count", "created", "-created", "discounted_price", "-discounted_price"]
        mobile_courses = []
        for order in ordering:
            if order in allowed_ordering:
                if order == "-ratings":
                   course_list.sort(key=lambda x: (x.ratings is None, x.ratings), reverse=True)
                elif order == "ratings":
                    course_list.sort(key=lambda x: (x.ratings is None, x.ratings))
                if order == "-enrollments_count":
                   course_list.sort(key=lambda x: (x.enrollments_count is None, x.enrollments_count), reverse=True)
                elif order == "enrollments_count":
                    course_list.sort(key=lambda x: (x.enrollments_count is None, x.enrollments_count))
                if order == "-created":
                   course_list.sort(key=lambda x: (x.created is None, x.created), reverse=True)
                elif order == "created":
                    course_list.sort(key=lambda x: (x.created is None, x.created))
                if order == "-discounted_price":
                   course_list.sort(key=lambda x: (x.discounted_price is None, x.discounted_price), reverse=True)
                elif order == "discounted_price":
                    course_list.sort(key=lambda x: (x.discounted_price is None, x.discounted_price))

        return course_list


class WebCourseListView(CourseListView):
    """ List courses and modes. """
    class CourseListPageNumberPagination(LazyPageNumberPagination):
        max_page_size = 100
    authentication_classes = (JwtAuthentication,BearerAuthentication,SessionAuthentication)
    permission_classes = ((AllowAny,))
    serializer_class = WebCourseSerializer
    pagination_class = CourseListPageNumberPagination
    # filter_class = CourseListFilter
    # filterset_class = CourseListFilter
    # filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        filtered_courses = []
        mobile_courses = []
        filter = False
        filters = {"enrollments_count":None,'difficulty_level': None, 'sale_type': None, 'subcategory_id': None, 'platform_visibility' : None , 'category' : None, 'discount_applicable': 'Boolean', 'is_premium': 'Boolean'}
        request_filters = {}
        for f,val in filters.items():
            filter_val = self.request.query_params.get(f, None)
            if filter_val is not None:
                filter = True
                if val == 'Boolean':
                    boolean_result = [json.loads(filter_val.split(',')[0].lower())]
                    request_filters[f] = boolean_result
                else:
                    request_filters[f] = filter_val.split(',')

        courses = list(WebCourse.iterator())
        platform_only_courses = []

        for course in courses:
            platform = course.platform_visibility
            if 'platform_visibility' in request_filters.keys():
                request_filters['platform_visibility'].append('both')
                if platform == None or platform in request_filters['platform_visibility']:
                    platform_only_courses.append(course)
            else:
                if platform == None or platform == "both":
                    platform_only_courses.append(course)
        courses = platform_only_courses

        try:
            platform_courses_list = []
            user = self.request.user
            user_org = user.user_extra_info.organization
            authorization = self.request.META.get('HTTP_AUTHORIZATION')

            if "JWT" not in authorization:
                for course in courses:
                    try:
                        course_overview = CourseOverview.get_from_id(course.id)
                        platform = course_overview.platform_visibility
                        organization = course_overview.organization
                        if user.is_staff:
                            platform_courses_list.append(course)
                        elif user_org == organization or organization == None:
                            platform_courses_list.append(course)
                        elif organization == None and user_org == None:
                            platform_courses_list.append(course)
                    except:
                        pass
                courses = platform_courses_list

            else:
                for course in courses:
                    try:
                        course_overview = CourseOverview.get_from_id(course.id)
                        platform = course_overview.platform_visibility
                        organization = course_overview.organization
                        if organization == None:
                            platform_courses_list.append(course)
                    except:
                        pass
                courses = platform_courses_list

        except:
            platform_courses_list = []
            for course in courses:
                try:
                    course_overview = CourseOverview.get_from_id(course.id)
                    platform = course_overview.platform_visibility
                    organization = course_overview.organization
                    if organization == None:
                        platform_courses_list.append(course)
                except:
                    pass
            courses = platform_courses_list

        ordering_filter=self.request.query_params.get('ordering', None)
        if ordering_filter:
            ordering_filter_list = ordering_filter.split(',')
            courses = self.order_courses(courses, ordering_filter_list)
        if filter:
            for course in courses:
                is_filter = [True if getattr(course,f) in val and val is not None else False for f,val in request_filters.items()]
                if all(is_filter):
                    filtered_courses.append(course)
        if self.request.query_params.get('coursename', None):
            filtered_courses_list = []
            course_list = filtered_courses if len(filtered_courses) > 0 else courses
            for course in course_list:
                search_string = self.request.query_params.get('coursename').lower()
                if course.name.lower().find(search_string) > -1: #and course.platform_visibility in ['mobile', 'both', 'Mobile', 'Both', None]:
                    filtered_courses_list.append(course)

            return filtered_courses_list

        if not self.request.query_params.get('coursename', None) and not filter:
            return courses

        return filtered_courses


@view_auth_classes(is_authenticated=True)
class CourseDetailView(RetrieveAPIView):
    serializer_class = CourseDetailSerializer
    def get_object(self):
        course_key = self.kwargs['course_key_string']
        course_id = CourseKey.from_string(course_key)
        course = get_course_by_id(course_id)

        try:
            course_modes = CourseMode.objects.filter(course_id=course_id)
            course.modes = course_modes
            course_overview = CourseOverview.get_from_id(course_id)
            if course_overview.platform_visibility == "Web":
                response = {"status": False, "message":"Course platform doesn't match the requirments", "result":None, "status_code": 404}
            course.image_urls = course_overview.image_urls
            course_extra_info = Course(course.id,list(course_modes),user=self.request.user)
            course.enrollments_count = course_extra_info.enrollments_count
            course.ratings = float("{:.2f}".format(course_extra_info.ratings))
            course.comments_count = course_extra_info.comments_count
            course.difficulty_level = course.difficulty_level.capitalize() if course.difficulty_level else "Unknown"
            course.discount_applicable = course_extra_info.discount_applicable
            course.discount_percentage = course_extra_info.discount_percentage_string
            course.discounted_price = course_extra_info.discounted_price
            course.currency = course_extra_info.currency
            course.description = course_overview.short_description
            course_usage_key = modulestore().make_course_usage_key(course_id)
            response = get_blocks(self.request,course_usage_key,self.request.user,requested_fields=['completion'],block_types_filter='vertical')
            course.chapter_count = len(response['blocks'])
            course.name = course_overview.display_name
            course.allow_review = course_overview.allow_review
            course.is_enrolled = CourseEnrollment.is_enrolled(self.request.user, course_id)
            course.own_feedback = CourseReview.is_reviewed(self.request.user, course_id)
            course.discount_type = course_extra_info.discount_type
            course.voucher_applicable = course_extra_info.coupon_applicable
            course.available_vouchers = course_extra_info.available_vouchers

            if len(course_extra_info.modes) == 0:
                course.price = 0
            else:
                course.price = course_extra_info.modes[0].min_price
            return course
        except Exception as e:
            response = {"status": False, "message":e, "result":None, "status_code": 500}
            return response

@view_auth_classes(is_authenticated=True)
class WebCourseDetailView(CourseDetailView):
    serializer_class = WebCourseDetailSerializer
    def get_object(self):
        course_key = self.kwargs['course_key_string']
        course_id = CourseKey.from_string(course_key)
        course = get_course_by_id(course_id)

        try:
            course_modes = CourseMode.objects.filter(course_id=course_id)
            course.modes = course_modes
            course_overview = CourseOverview.get_from_id(course_id)
            if course_overview.platform_visibility == "Web":
                response = {"status": False, "message":"Course platform doesn't match the requirments", "result":None, "status_code": 404}
            course.image_urls = course_overview.image_urls
            course_extra_info = Course(course.id,list(course_modes),user=self.request.user)
            course.enrollments_count = course_extra_info.enrollments_count
            course.ratings = float("{:.2f}".format(course_extra_info.ratings))
            course.comments_count = course_extra_info.comments_count
            course.difficulty_level = course.difficulty_level.capitalize() if course.difficulty_level else "Unknown"
            course.discount_applicable = course_extra_info.discount_applicable
            course.discount_percentage = course_extra_info.discount_percentage
            course.discount_percentage_string = course_extra_info.discount_percentage_string
            course.discounted_price = float(course_extra_info.discounted_price)
            course.discounted_price_string = str(course_extra_info.discounted_price)
            course.currency = course_extra_info.currency
            course.description = course_overview.short_description
            course_usage_key = modulestore().make_course_usage_key(course_id)
            response = get_blocks(self.request,course_usage_key,self.request.user,requested_fields=['completion'],block_types_filter='vertical')
            course.chapter_count = len(response['blocks'])
            course.name = course_overview.display_name
            course.allow_review = course_overview.allow_review
            course.is_enrolled = CourseEnrollment.is_enrolled(self.request.user, course_id)
            course.own_feedback = CourseReview.is_reviewed(self.request.user, course_id)

            if len(course_extra_info.modes) == 0:
                course.price = 0
            else:
                course.price = course_extra_info.modes[0].min_price
            return course
        except Exception as e:
            response = {"status": False, "message":e, "result":None, "status_code": 500}
            return response


@api_view(['POST'])
@authentication_classes((BearerAuthentication,SessionAuthentication,))
@permission_classes([IsAuthenticated])
def add_product_to_basket(request):

    """
    API: /commerce/v2/add_product/
    This API add a product in the basket of the user.
    """
    if request.method == 'POST':
        user = request.user
        api = ecommerce_api_client(user)
        try:
            for product in request.data['products']:
                course_mode = CourseMode.objects.get(sku=product['sku'])
                if course_mode.mode_slug == 'audit':
                    raise Exception("Free Product can not be added to the cart")
            response = api.baskets.post(request.data)
            if 'status_code' in response and response['status_code'] == 409:
                return HttpResponseBadRequest(response['message'])
            return Response(response)
        except Exception as e:
            return HttpResponseBadRequest(str(e))



@api_view(['POST'])
@authentication_classes((JwtAuthentication,SessionAuthentication,))
@permission_classes([IsAuthenticated])
def update_discount(request, sku):
    if CourseMode.objects.filter(sku=sku).exists():
        course_mode = CourseMode.objects.get(sku=sku)
        course_mode.discount_percentage = request.data['discount_percentage']
        course_mode.save()
        return Response({"result": "success"})









@view_auth_classes(is_authenticated=True)
class CourseCheckoutDetailView(RetrieveAPIView):
    serializer_class = CourseDetailCheckoutSerializer
    def get_object(self):
        course_key = self.kwargs['course_key_string']
        course_id = CourseKey.from_string(course_key)
        course = get_course_by_id(course_id)

        try:
            course_modes = CourseMode.objects.filter(course_id=course_id)
            course.modes = course_modes
            course_overview = CourseOverview.get_from_id(course_id)
            if course_overview.platform_visibility == "Web":
                response = {"status": False, "message":"Course platform doesn't match the requirments", "result":None, "status_code": 404}
            course.image_urls = course_overview.image_urls
            course_extra_info = Course(course.id,list(course_modes),user=self.request.user)
            course.enrollments_count = course_extra_info.enrollments_count
            course.ratings = float("{:.2f}".format(course_extra_info.ratings))
            course.comments_count = course_extra_info.comments_count
            course.difficulty_level = course.difficulty_level.capitalize() if course.difficulty_level else "Unknown"
            course.discount_applicable = course_extra_info.discount_applicable
            course.discount_percentage = course_extra_info.discount_percentage
            course.discounted_price = course_extra_info.discounted_price
            course.currency = course_extra_info.currency
            course.description = course_overview.short_description
            course_usage_key = modulestore().make_course_usage_key(course_id)
            response = get_blocks(self.request,course_usage_key,self.request.user,requested_fields=['completion'],block_types_filter='vertical')
            course.chapter_count = len(response['blocks'])
            course.name = course_overview.display_name
            course.new_category = course_overview.new_category if course_overview.new_category else "None"
            course.organization = course.display_org_with_default
            course.available_vouchers = course_extra_info.available_vouchers
            if len(course_extra_info.modes) == 0:
                course.price = 0
            else:
                course.price = course_extra_info.modes[0].min_price
            return course
        except Exception as e:
            response = {"status": False, "message":e, "result":None, "status_code": 500}
            return response




@api_view()
@authentication_classes((BearerAuthentication,SessionAuthentication,))
@permission_classes([IsAuthenticated])
def get_basket_content(request,id=None):

    user = request.user
    api = ecommerce_api_client(user)
    if id:
        response = api.basket_details.get(id=id)
    else:
        response = api.basket_details.get()
    if response['status_code'] == 404:
        return HttpResponseNotFound(response['message'])
    return Response(response)


@api_view()
@authentication_classes((BearerAuthentication,SessionAuthentication,))
@permission_classes([IsAuthenticated])
def get_basket_content_mobile(request,id=None):

    user = request.user
    api = ecommerce_api_client(user)
    if id:
        response = api.basket_details.get(id=id)
    else:
        response = api.basket_details_mobile.get()
        log.info("==============")
        log.info(response)
    if response['status_code'] == 404:
        return HttpResponseNotFound(response['message'])
    return Response(response)


