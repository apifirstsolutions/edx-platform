""" Custom API permissions. """


from django.contrib.auth.models import User
from rest_framework.permissions import BasePermission, DjangoModelPermissions

from openedx.core.lib.api.permissions import ApiKeyHeaderPermission

from lms.djangoapps.commerce.utils import is_account_activation_requirement_disabled

class ApiKeyOrModelPermission(BasePermission):
    """ Access granted for requests with API key in header,
    or made by user with appropriate Django model permissions. """
    def has_permission(self, request, view):
        return ApiKeyHeaderPermission().has_permission(request, view) or DjangoModelPermissions().has_permission(
            request, view)

