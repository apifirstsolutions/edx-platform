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
    url_list["top_rated_courses"] = '/api/commerce/v2/courses/?platform_visibility=mobile&ordering=enrollments_count'
    url_list["free_courses"] = '/api/commerce/v2/courses/?platform_visibility=mobile&sale_type=free'
    headers = {
        'Authorization': bearer_token_from_request
    }
    http = 'http://'
    response_obj = {"message": "ERROR", "net_response_chunk": {}, "status": False, "status_code": 500}
    error_flag = True
    try:
        for key, api_url in url_list.items():
            actual_request = requests.get(http+base+api_url, headers=headers)
            data = actual_request.json()
            home_page_url[key] = data
            error_flag = False
    except Exception as ex:
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^", ex)
        error_flag = True
        pass
    if not error_flag:
        response_obj['status_code'] =status.HTTP_200_OK
        response_obj['status'] = True
        response_obj['net_response_chunk'] = home_page_url if home_page_url else ""
        response_obj['message'] = ""
        return Response(response_obj)
    else:
        return Response(response_obj)
