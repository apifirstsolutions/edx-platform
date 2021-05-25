from datetime import datetime
from common.djangoapps.util.date_utils import strftime_localized
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from lms.djangoapps.commerce.utils import EcommerceService
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.user_api.accounts.settings_views import get_user_orders
from openedx.core.lib.api.authentication import BearerAuthentication


class LHUBOrdersHistoryView(APIView):

    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication)
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        **Example Request**

        /lhub_extended_api/orders

        **Example GET Response**

        {
            "message": "",
            "status": true,
            "status_code": 200,
            "result": [
                {
                    "number": "EDX-100002",
                    "price": "149.00",
                    "order_date": "Apr 14, 2021",
                    "receipt_url": "http://localhost:18130/checkout/receipt/?order_number=EDX-100002",
                    "lines": [
                        {
                            "title": "Seat in edX Demonstration Course with verified certificate (and ID verification)",
                            "quantity": 1,
                            "description": "Seat in edX Demonstration Course with verified certificate (and ID verification)",
                            "status": "Complete",
                            "line_price_excl_tax": "149.00",
                            "unit_price_excl_tax": "149.00",
                            "product": {
                                "id": 3,
                                "url": "http://edx.devstack.ecommerce:18130/api/v2/products/3/",
                                "structure": "child",
                                "product_class": "Seat",
                                "title": "Seat in edX Demonstration Course with verified certificate (and ID verification)",
                                "price": "149.00",
                                "expires": "2022-03-29T13:18:02.483296Z",
                                "attribute_values": [
                                    {
                                        "name": "certificate_type",
                                        "code": "certificate_type",
                                        "value": "verified"
                                    },
                                    {
                                        "name": "course_key",
                                        "code": "course_key",
                                        "value": "course-v1:edX+DemoX+Demo_Course"
                                    },
                                    {
                                        "name": "id_verification_required",
                                        "code": "id_verification_required",
                                        "value": true
                                    }
                                ],
                                "is_available_to_buy": true,
                                "stockrecords": [
                                    {
                                        "id": 3,
                                        "product": 3,
                                        "partner": 1,
                                        "partner_sku": "8CF08E5",
                                        "price_currency": "USD",
                                        "price_excl_tax": "149.00"
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        """
        try:
            user_orders = get_user_orders(request.user)
        except:
            return Response(
                status=400,
                data={
                    "message": "Error fetching order history",
                    "status": False,
                    "status_code": 400,
                    "result": []
                }
            )

        [update_order_format(order) for order in user_orders]

        return Response(
            {
                "message": "",
                "status": True,
                "status_code": 200,
                "result": user_orders
            }
        )


class LHUBOrderDetailView(APIView):

    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication)
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        """
        **Example Request**

        /lhub_extended_api/orders/<order_number>

        **Example GET Response**

        {
            "message": "",
            "status": true,
            "status_code": 200,
            "result": {
                "billing_address": {
                    "first_name": "staff",
                    "last_name": "real",
                    "line1": "qwerty",
                    "line2": "12",
                    "postcode": "",
                    "state": "",
                    "country": "AG",
                    "city": "krakow"
                },
                "currency": "USD",
                "discount": "0",
                "lines": [
                    {
                        "title": "Seat in edX Demonstration Course with verified certificate (and ID verification)",
                        "quantity": 1,
                        "description": "Seat in edX Demonstration Course with verified certificate (and ID verification)",
                        "status": "Complete",
                        "line_price_excl_tax": "149.00",
                        "unit_price_excl_tax": "149.00",
                        "product": {
                            "id": 3,
                            "url": "http://edx.devstack.ecommerce:18130/api/v2/products/3/",
                            "structure": "child",
                            "product_class": "Seat",
                            "title": "Seat in edX Demonstration Course with verified certificate (and ID verification)",
                            "price": "149.00",
                            "expires": "2022-03-29T13:18:02.483296Z",
                            "is_available_to_buy": true,
                            "stockrecords": [
                                {
                                    "id": 3,
                                    "product": 3,
                                    "partner": 1,
                                    "partner_sku": "8CF08E5",
                                    "price_currency": "USD",
                                    "price_excl_tax": "149.00"
                                }
                            ],
                            "course_id": "course-v1:edX+DemoX+Demo_Course",
                            "course_image_url": "/asset-v1:edX+DemoX+Demo_Course+type@asset+block@images_course_image.jpg"
                        }
                    }
                ],
                "number": "EDX-100002",
                "payment_processor": "cybersource",
                "status": "Complete",
                "user": {
                    "email": "staff@example.com",
                    "username": "staff"
                },
                "vouchers": [],
                "payment_method": "1111 Visa",
                "order_date": "Apr 14, 2021",
                "receipt_url": "http://localhost:18130/checkout/receipt/?order_number=EDX-100002",
                "items_total": "149.00",
                "subtotal": "149.00",
                "gst": "0.0"
            }
        }
        """
        try:
            user_order = get_user_order(request.user, order_number)
        except:
            return Response(
                status=400,
                data={
                    "message": "Error fetching order history",
                    "status": False,
                    "status_code": 400,
                    "result": []
                }
            )

        if user_order:
            update_order_format(user_order)

        return Response(
            data={
                "message": "",
                "status": True,
                "status_code": 200,
                "result": user_order
            }
        )


def update_order_format(order):
    lines = order.get('lines', [])
    for line in lines:
        product = line.get('product', {})
        attribute_values = product.pop('attribute_values')

        course_id = next(attribute_value.get('value') for attribute_value in attribute_values if
                         attribute_value.get('code') == 'course_key')

        course = CourseOverview.objects.filter(id=course_id).first()
        product.update({
            "course_id": course_id,
            "course_image_url": course.course_image_url if course else ''
        })


def get_user_order(user, number):
    """Given a user, get the detail of all the orders from the Ecommerce service.

    Args:
        user (User): The user to authenticate as when requesting ecommerce.
        number (str): The number of specific order

    Returns:
        Dict, representing order returned by the Ecommerce service.
    """
    order = ecommerce_api_client(user).orders(number).get()

    if order['status'].lower() == 'complete':
        date_placed = datetime.strptime(order.pop('date_placed'), "%Y-%m-%dT%H:%M:%SZ")
        order.update({
            'order_date': strftime_localized(date_placed, 'SHORT_DATE'),
            'receipt_url': EcommerceService().get_receipt_page_url(order['number']),
            'items_total': order.pop('total_excl_tax'),
            'subtotal': order.pop('total_incl_tax'),
            'gst': str(order.pop('total_tax'))
        })

    return order
