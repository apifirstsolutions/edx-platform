"""HTTP end-points for the User API. """


from django.contrib.auth.models import User
from django.core.exceptions import NON_FIELD_ERRORS, PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django_filters.rest_framework import DjangoFilterBackend
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys import InvalidKeyError
from opaque_keys.edx import locator
from opaque_keys.edx.keys import CourseKey
from rest_framework import authentication, generics, status, viewsets
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from six import text_type

from openedx.core.djangoapps.django_comment_common.models import Role
from openedx.core.djangoapps.user_api import accounts
from openedx.core.lib.api.view_utils import require_post_params
from openedx.core.djangoapps.user_api.models import UserPreference
from openedx.core.djangoapps.user_api.preferences.api import get_country_time_zones, update_email_opt_in
from openedx.core.djangoapps.user_api.serializers import (
    CountryTimeZoneSerializer,
    UserPreferenceSerializer,
    UserSerializer
)
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission
from common.djangoapps.student.helpers import AccountValidationError
from common.djangoapps.util.json_request import JsonResponse

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from rest_framework.generics import RetrieveAPIView
import logging
from rest_framework.response import Response
from rest_framework import status    
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.http import Http404
from openedx.core.lib.api.authentication import BearerAuthentication

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    DRF class for interacting with the User ORM object
    """
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    queryset = User.objects.all().prefetch_related("preferences").select_related("profile")
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"


class ForumRoleUsersListView(generics.ListAPIView):
    """
    Forum roles are represented by a list of user dicts
    """
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"

    def get_queryset(self):
        """
        Return a list of users with the specified role/course pair
        """
        name = self.kwargs['name']
        course_id_string = self.request.query_params.get('course_id')
        if not course_id_string:
            raise ParseError('course_id must be specified')
        course_id = CourseKey.from_string(course_id_string)
        role = Role.objects.get_or_create(course_id=course_id, name=name)[0]
        users = role.users.prefetch_related("preferences").select_related("profile").all()
        return users


class UserPreferenceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    DRF class for interacting with the UserPreference ORM
    """
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    queryset = UserPreference.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("key", "user")
    serializer_class = UserPreferenceSerializer
    paginate_by = 10
    paginate_by_param = "page_size"


class PreferenceUsersListView(generics.ListAPIView):
    """
    DRF class for listing a user's preferences
    """
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"

    def get_queryset(self):
        return User.objects.filter(
            preferences__key=self.kwargs["pref_key"]
        ).prefetch_related("preferences").select_related("profile")


class UpdateEmailOptInPreference(APIView):
    """View for updating the email opt in preference. """
    authentication_classes = (SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    @method_decorator(require_post_params(["course_id", "email_opt_in"]))
    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        """ Post function for updating the email opt in preference.

        Allows the modification or creation of the email opt in preference at an
        organizational level.

        Args:
            request (Request): The request should contain the following POST parameters:
                * course_id: The slash separated course ID. Used to determine the organization
                    for this preference setting.
                * email_opt_in: "True" or "False" to determine if the user is opting in for emails from
                    this organization. If the string does not match "True" (case insensitive) it will
                    assume False.

        """
        course_id = request.data['course_id']
        try:
            org = locator.CourseLocator.from_string(course_id).org
        except InvalidKeyError:
            return HttpResponse(
                status=400,
                content=u"No course '{course_id}' found".format(course_id=course_id),
                content_type="text/plain"
            )
        # Only check for true. All other values are False.
        email_opt_in = request.data['email_opt_in'].lower() == 'true'
        update_email_opt_in(request.user, org, email_opt_in)
        return HttpResponse(status=status.HTTP_200_OK)


class CountryTimeZoneListView(generics.ListAPIView):
    """
    **Use Cases**

        Retrieves a list of all time zones, by default, or common time zones for country, if given

        The country is passed in as its ISO 3166-1 Alpha-2 country code as an
        optional 'country_code' argument. The country code is also case-insensitive.

    **Example Requests**

        GET /user_api/v1/preferences/time_zones/

        GET /user_api/v1/preferences/time_zones/?country_code=FR

    **Example GET Response**

        If the request is successful, an HTTP 200 "OK" response is returned along with a
        list of time zone dictionaries for all time zones or just for time zones commonly
        used in a country, if given.

        Each time zone dictionary contains the following values.

            * time_zone: The name of the time zone.
            * description: The display version of the time zone
    """
    serializer_class = CountryTimeZoneSerializer
    paginator = None

    def get_queryset(self):
        country_code = self.request.GET.get('country_code', None)
        return get_country_time_zones(country_code)



@api_view()
@authentication_classes((BearerAuthentication,))
@permission_classes([IsAuthenticated])
def get_ephemeral_key(request):

    requested_params = request.query_params.copy()
    if requested_params.get('stripe_customer_id', None):
        stripe_customer_id = requested_params.get('stripe_customer_id')
        User = get_user_model()
        api_user = User.objects.get(username="ecommerce_worker")
        api = ecommerce_api_client(api_user)
        res = api.stripe_get_ephemeral_key.get(stripe_customer_id=stripe_customer_id)
        if 'result' in res.keys():
            return Response(res['result'])
        else:
            logging.info('=====view 404 =====')
            raise Http404("Customer with this id do not exist")        

