import logging
import json

from rest_framework.decorators import api_view

from django.contrib.auth import get_user_model
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from requests.exceptions import ConnectionError, Timeout
from edx_rest_api_client.exceptions import SlumberBaseException
from rest_framework import status
from rest_framework.response import Response


User = get_user_model()
log = logging.getLogger(__name__)

@api_view(['POST'])
# by default it's api_view(['GET'])
def course_modification(request, course_id):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    # content = body['course_key']

    course_key = course_id
    display_name = body['display_name']
    course_type = body['course_type']
    course_price = body['course_price']

    product_list = []
    attribute_values_list = []
    attribute_values = {'name': 'id_verification_required', 'value': False}
    if course_type == 'professional':
        attribute_values_list.append({'name': 'certificate_type', 'value': 'professional'})
    attribute_values_list.append(attribute_values)
    product = {'course': {'id': course_key, 'name': display_name, 'type': course_type,
        'verification_deadline': None, 'honor_mode': False}, 'expires': None,
        'price': course_price, 'product_class': 'Seat', 'attribute_values': attribute_values_list}
    product_list.append(product)
    data = {'id': course_key, 'name': display_name, 'verification_deadline': None,
        'products': product_list}
    # print(data)

    user = User.objects.get(username="ecommerce_worker")
    api_user = user
    api = ecommerce_api_client(api_user)
    try:
        res = api.publication.post(data)
        # return True
        # return Response(data)
        return Response({'status': 'Success'}, status=status.HTTP_200_OK)
    except (ConnectionError, SlumberBaseException, Timeout):
        log.exception('Failed to publish the course: %s',course_key)
        # return False
        # return Response(data)
        return Response({'status': 'Failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

