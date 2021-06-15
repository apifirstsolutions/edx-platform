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
# from rest_framework.viewsets import GenericViewSet

# from .serializers import (
#   BundleSerializer, 
#   SubscriptionPlanSerializer,
#   SubscriptionSerializer, 
# )

log = logging.getLogger(__name__)


# TODO       
# class SubscriptionViewSet(
#   GenericViewSet,
#   CreateModelMixin,
#   RetrieveModelMixin,
#   UpdateModelMixin,
#   ListModelMixin):

#   serializer_class = SubscriptionSerializer
#   queryset = Subscription.objects.all()
#   http_method_names = ['get', 'post', 'patch']

#   def _cancel_subscription(subscription, new_status):
#     if subscription.user is not None and \
#       subscription.status in [ Statuses.ACTIVE.value, Statuses.INACTIVE.value ] and \
#       new_status in [ Statuses.CANCELLED.value, Statuses.EXPIRED.value ]:

#       svc = SubscriptionService()
#       return svc.cancel_subscription(subscription)


#   def update(self, request, pk=None):
#     """
#     Disabled. Go to Django Admin to edit Subscriptions
#     """
#     pass

#   def partial_update(self, request, pk=None):
#     """
#     Use only to Cancel or Expire an active, non-enterprise Subscriptions.
#     """

#     try:
#       subscription = Subscription.objects.get(id=pk)

#       if subscription is not None and request.data['status'] is not None:
#         new_status = request.data['status']

#         if subscription.user is not None and \
#           subscription.status in [ Statuses.ACTIVE.value, Statuses.INACTIVE.value ] and \
#           new_status in [ Statuses.CANCELLED.value, Statuses.EXPIRED.value ]:

#           svc = SubscriptionService()
#           result = svc.cancel_subscription(subscription)
          
#           if not result['success']:
#             return JsonResponse(result)
#           else:
#             subscription.status = new_status
#             subscription.save()
#             return JsonResponse(result)
#       else:
#         return Response(
#           { 'message': "Use only to Cancel or Expire an active, non-enterprise Subscriptions." }, 
#           status=HTTP_400_BAD_REQUEST
#         )
#     except Exception as e:
#       log.error()
#       raise

