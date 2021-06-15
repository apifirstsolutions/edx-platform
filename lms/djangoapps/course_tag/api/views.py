"""
API views for CourseTag
"""
from collections import OrderedDict

from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework.generics import ListAPIView
from openedx.core.lib.api.view_utils import LazySequence
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from lms.djangoapps.course_tag.models import CourseTag, CourseTagType
from .serializers import CourseTagTypeSerializer
from rest_framework import pagination
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework import status
import requests
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from openedx.core.lib.api.authentication import BearerAuthentication

from logging import getLogger
logger = getLogger(__name__)
#
class LazyPageNumberPagination(pagination.PageNumberPagination):

    page_size = 100
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


@api_view(['GET'])
@authentication_classes((BearerAuthentication, SessionAuthentication, JwtAuthentication))
@permission_classes([IsAuthenticated])
def get_courses_by_course_tag(request):
    course_tag_consolidated_response = {}
    base = request.get_host()
    bearer_token_from_request = request.META.get('HTTP_AUTHORIZATION')
    # For ios system limitation, Processing API is kep it in the Backend of LXP(for calling Listing and Detailed API).
    url_listing_api  = '/api/course_tag/type'
    url_detail_api = '/api/commerce/v2/courses?course_tag_type='
    headers = {
        'Authorization': bearer_token_from_request
    }
    http = 'http://'
    response_obj = {"message": "Error", "result": {}, "status": False, "status_code": 401}
    error_flag = True
    net_response = []
    try:
        response_tags = requests.get(http + base + url_listing_api, headers=headers)
        data = response_tags.json()
        for tag_name in data['result']['results']:
            course_tag_consolidated_response['collectionTitle'] = tag_name['display_name']
            course_tag_consolidated_response['collectionId'] = tag_name['id'] if tag_name['display_name'] else ""
            if tag_name['display_name'] and data['status_code'] == 200:
                url_ = url_detail_api + str(tag_name['display_name'])
                response_courses= requests.get(http + base + url_, headers=headers)
                detailed_data = response_courses.json()
                if detailed_data['status_code'] == 200:
                    # limiting courses to 10 per course Tag Type for quick response so no pagination required
                    course_tag_consolidated_response['courses'] = detailed_data['result']['results'][:10]
                    error_flag = False
                else:
                    error_flag = True
            else:
                error_flag = True
            result_copy = course_tag_consolidated_response.copy()
            net_response.append(result_copy)
    except Exception as ex:
        #dont' expose the specify error internal to system to outside API, Put it in generic manner
        logger.error("Error while using Course Tag Processing API - Exception as %s", ex)
        response_obj = {"message": "ERROR", "net_response_chunk": {}, "status": False,
                        "status_code": 500}
        error_flag = True

    if not error_flag:
        response_obj['status_code'] =status.HTTP_200_OK
        response_obj['status'] = True
        response_obj['result'] = net_response
        response_obj['message'] = ""
        return Response(response_obj)
    else:
        return Response(response_obj)

