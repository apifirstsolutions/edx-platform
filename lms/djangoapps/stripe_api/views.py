from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from openedx.core.lib.api.authentication import BearerAuthentication
from rest_framework.permissions import IsAuthenticated
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
import logging
from rest_framework.authentication import SessionAuthentication


@api_view(['POST'])
@authentication_classes((BearerAuthentication,))
@permission_classes([IsAuthenticated])
def get_customer_id(request):

    """
    API: /stripe_api/profile/?email={email_address}
    This function is used to send the stripe customer_id saved in user context and if it doesn't exist create one and return.
    """
    if request.method == 'POST':
        user = request.user
        api = ecommerce_api_client(user)
        try:
            response = api.stripe_api.post(request.POST)
            return Response(response)
        except Exception as e:
            return Response({'message':e, 'status': True, 'result':{}, 'status_code':200})

@api_view(['POST'])
@authentication_classes((BearerAuthentication,))
@permission_classes([IsAuthenticated])
def checkout_payment(request):

    """
    This fucntion is used to make payment.
    """
    if request.method == 'POST':
        user = request.user
        api = ecommerce_api_client(user)
        try:
            response =  api.stripe_payment.post(request.POST)
            return Response(response)
        except Exception as e:
            return Response({'message':e, 'status': True, 'result':{}, 'status_code':200})

@api_view(['POST'])
@authentication_classes((BearerAuthentication,))
@permission_classes([IsAuthenticated])
def checkout_payment_intent(request):

    """
    This fucntion is used to make payment.
    """
    if request.method == 'POST':
        user = request.user
        api = ecommerce_api_client(user)
        try:
            response =  api.checkout_payment_intent.post(request.POST)
            return Response(response)
        except Exception as e:
            return Response({'message':e, 'status': True, 'result':{}, 'status_code':200})


@api_view(['POST'])
@authentication_classes((BearerAuthentication,))
@permission_classes([IsAuthenticated])
def confirm_payment_intent(request):

    """
    This fucntion is used to make payment.
    """
    if request.method == 'POST':
        user = request.user
        api = ecommerce_api_client(user)
        try:
            response =  api.confirm_payment_intent.post(request.POST)
            return Response(response)
        except Exception as e:
            return Response({'message':e, 'status': True, 'result':{}, 'status_code':200})

@api_view(['POST'])
@authentication_classes((BearerAuthentication,SessionAuthentication))
@permission_classes([IsAuthenticated])
def custom_basket(request):

    """
    This fucntion is used to delete item from basket.
    """
    if request.method == 'POST':
        user = request.user
        api = ecommerce_api_client(user)
        try:
            response =  api.custom_baskets.post(request.POST)
            return Response(response)
        except Exception as e:
            return Response({'message':e, 'status': True, 'result':{}, 'status_code':200})

@api_view(['GET'])
@authentication_classes((BearerAuthentication,SessionAuthentication))
@permission_classes([IsAuthenticated])
def basket_item_count(request):
    return Response({"status":False,"status_code":200,"result":{"number_of_item":0},"message":""})
            
    """
    This function is used to return number of items in the basket.
    """
    if request.method == 'GET':
        user = request.user
        api = ecommerce_api_client(user)
        try:
            response =  api.basket_item_count.get()
            return Response(response)
        except Exception as e:
            return Response({'message':e, 'status': False, 'result':{}, 'status_code':400})

@api_view(['POST'])
@authentication_classes((BearerAuthentication,SessionAuthentication))
@permission_classes([IsAuthenticated])
def basket_buy_now(request):
    """
    This function is used to buyitem without adding it to cart.
    """
    if request.method == 'POST':
        user = request.user
        api = ecommerce_api_client(user)
        try:
            response = api.basket_buy_now.post(request.data)
            if "developer_message" in response:
                return Response({
                'message': response["developer_message"],
                'status': False,
                'result':{},
                'status_code':400
            })
            else:
                return Response({
                    'message': '',
                    'status': True,
                    'result':response,
                    'status_code':200
            })
        except Exception as e:
            return Response({'message':e, 'status': False, 'result':{}, 'status_code':400})

@api_view(['DELETE'])
@authentication_classes((BearerAuthentication,SessionAuthentication))
@permission_classes([IsAuthenticated])
def basket_buy_now_cancel(request):
    """
    This function is used to remove buyitem without adding it to cart.
    """
    if request.method == 'DELETE':
        user = request.user
        api = ecommerce_api_client(user)
        try:
            response = api.basket_buy_now.delete()
            return Response(response)
        except Exception as e:
            return Response({'message':e, 'status': False, 'result':{}, 'status_code':400})
