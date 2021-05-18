from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
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
                ]
            }
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

        target_order = next((order for order in user_orders if order['number'] == order_number), {})

        if target_order:
            update_order_format(target_order)

        return Response(
            data={
                "message": "",
                "status": True,
                "status_code": 200,
                "result": target_order
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
