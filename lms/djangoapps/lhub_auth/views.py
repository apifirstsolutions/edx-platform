import logging
from django.http import JsonResponse

# from rest_framework.mixins import (
#     CreateModelMixin, 
#     ListModelMixin, 
#     RetrieveModelMixin, 
#     UpdateModelMixin
# )
# from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated

from rest_framework.views import APIView
from lms.envs.common import SCID_INTERNAL_API_URL
# from rest_framework.viewsets import GenericViewSet

# from .serializers import (
#   BundleSerializer, 
#   SubscriptionPlanSerializer,
#   SubscriptionSerializer, 
# )

log = logging.getLogger(__name__)


class ScidCustomerView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        lhub_customer_id = kwargs.get('id')

        # TODO  proxy request to SCID_INTERNAL_API_URL/scid/customer/<lhub_customer_id>
    
        
        return Response(kwargs)
       