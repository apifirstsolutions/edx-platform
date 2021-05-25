"""
API views for banner
"""

from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import APIException, NotFound
from lms.djangoapps.banner.models import Banner
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from .serializers import BannerSerializer
from rest_framework import status
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.permissions import IsAuthenticated
from edx_rest_framework_extensions.paginators import NamespacedPageNumberPagination
from django.core.paginator import InvalidPage
from rest_framework.serializers import ValidationError
from rest_framework.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR

from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response


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
class BannerApi(DeveloperErrorViewMixin, ListAPIView):

    class BannerApiPageNumberPagination(LazyPageNumberPagination):
        max_page_size = 100

    pagination_class = BannerApiPageNumberPagination
    serializer_class = BannerSerializer
    authentication_classes = (
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
        JwtAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    # def get_queryset(self):
    #     """
    #     The query will return 1 to 10 images of banner, platform is both(mobile, web) or mobile alone as of now
    #     """
    #     queryset = Banner.objects.filter(platform__in=['MOBILE', 'BOTH'], enabled=True)
    #     return queryset
    #     # raise CustomAPIException("Invalid course ID.", status_code=status.HTTP_404_NOT_FOUND)

    def get(self, request, format=None):
        banners = Banner.objects.filter(platform__in=['MOBILE', 'BOTH'], enabled=True)
        serializer = BannerSerializer(banners, many=True)
        result = {"results":serializer.data}
        pagination = {"next":None, "previous": None, "count": 1, "num_pages": 1 if len(serializer.data)<=100 else int(len(serializer.data)/100)}
        x = Response({"message": "", "result": result, "pagination":pagination, "status": True, "status_code": 200})
        if x and serializer.data:
            return x
        elif not serializer.data:
            return Response({"message": "No data found", "result": result, "pagination":pagination, "status": True, "status_code": 200})
        else:
            return Response({"message": "Error", "result": result, "pagination":pagination, "status": False, "status_code": 400})


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

"""
API views for Mobile Home page
"""


from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from openedx.core.lib.api.authentication import BearerAuthentication
from rest_framework.authentication import SessionAuthentication
import requests
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from logging import getLogger
#from ..decorators import mobile_view
from lms.djangoapps.mobile_api.utils import API_V05, API_V1
logger = getLogger(__name__)

@api_view(['GET'])
@authentication_classes((BearerAuthentication, SessionAuthentication, JwtAuthentication))
@permission_classes([IsAuthenticated])
def mobile_home_page(request):
    home_page_url = {}
    base = request.get_host()
    bearer_token_from_request = request.META.get('HTTP_AUTHORIZATION')

    url_list  = dict()
    url_list["banner"] = '/api/banner/details/'
    url_list["category"] = '/api/courses/v2/courses/categories/?page=1&page_size=1000'
    url_list['recommended_courses'] = '/api/courses/v2/recommended/courses/?page=1&page_size=10'
    url_list["most_popular"] = '/api/commerce/v2/courses/?platform_visibility=mobile&ordering=enrollments_count'
    url_list["top_rated_courses"] = '/api/commerce/v2/courses/?platform_visibility=mobile&ordering=-ratings'
    url_list["free_courses"] = '/api/commerce/v2/courses/?platform_visibility=mobile&sale_type=free'
    headers = {
        'Authorization': bearer_token_from_request
    }
    http = 'http://'
    response_obj = {"message": "Authentication Failed ", "net_response_chunk": {}, "status": False, "status_code": 401}
    error_flag = True
    response_code_list = []
    api_version = 'v1' 
    if api_version:
        try:
            for key, api_url in url_list.items():
                actual_request = requests.get(http+base+api_url, headers=headers)
                data = actual_request.json()
                home_page_url[key] = data
                response_code_list.append(data['status_code'])
        except Exception as ex:
            #dont' expose the specify error internal to system to outside API, Put it in generic manner
            logger.error("Error while processing mobile home API - Exception as %s", ex)
            response_obj = {"message": "ERROR", "net_response_chunk": {}, "status": False,
                            "status_code": 500}
            error_flag = True
            pass
        response_final_codes = list(set(response_code_list))
        #stream line 200, 202 and 500
        if len(response_final_codes) == 1 and response_final_codes[0] == 200:
            error_flag = False
        elif len(response_final_codes) >= 2 and 200 in response_final_codes:
            response_obj['status_code'] = status.HTTP_202_ACCEPTED
            response_obj['status'] = True
            response_obj['net_response_chunk'] = home_page_url if home_page_url else ""
            response_obj['message'] = "partial success"
            return Response(response_obj)
        else:
            error_flag = True

        if not error_flag:
            response_obj['status_code'] =status.HTTP_200_OK
            response_obj['status'] = True
            response_obj['net_response_chunk'] = home_page_url if home_page_url else ""
            response_obj['message'] = ""
            return Response(response_obj)
        else:
            return Response(response_obj)
    else:
        obj = {"message": "Wrong API version", "net_response_chunk": {}, "status": False, "status_code": 400}
        return Response(obj)
