"""
This module implements the upload and remove endpoints of the profile image api.
"""


import datetime
import itertools
import logging
from contextlib import closing

import base64
from django.core.files.base import ContentFile
import requests
from django.conf import settings


from django.utils.translation import ugettext as _
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from pytz import UTC
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from six import text_type
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_names, set_has_profile_image
from openedx.core.djangoapps.user_api.errors import UserNotFound
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.parsers import TypedFileUploadParser
from openedx.core.lib.api.permissions import IsUserInUrl
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin

from .exceptions import ImageValidationError
from .images import IMAGE_TYPES, create_profile_images, remove_profile_images, validate_uploaded_image, create_base64_profile_images

log = logging.getLogger(__name__)

LOG_MESSAGE_CREATE = u'Generated and uploaded images %(image_names)s for user %(user_id)s'
LOG_MESSAGE_DELETE = u'Deleted images %(image_names)s for user %(user_id)s'

from oauth2_provider.models import AccessToken as Token
from rest_framework.response import Response
import logging
from rest_framework.views import APIView
import requests
import json


def _make_upload_dt():
    """
    Generate a server-side timestamp for the upload. This is in a separate
    function so its behavior can be overridden in tests.
    """
    return datetime.datetime.utcnow().replace(tzinfo=UTC)


class ProfileImageView(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Add or remove profile images associated with user accounts.

        The requesting user must be signed in.  Users can only add profile
        images to their own account.  Users with staff access can remove
        profile images for other user accounts.  All other users can remove
        only their own profile images.

    **Example Requests**

        POST /api/user/v1/accounts/{username}/image

        DELETE /api/user/v1/accounts/{username}/image

    **Example POST Responses**

        When the requesting user attempts to upload an image for their own
        account, the request returns one of the following responses:

        * If the upload could not be performed, the request returns an HTTP 400
          "Bad Request" response with information about why the request failed.

        * If the upload is successful, the request returns an HTTP 204 "No
          Content" response with no additional content.

        If the requesting user tries to upload an image for a different
        user, the request returns one of the following responses:

        * If no user matches the "username" parameter, the request returns an
          HTTP 404 "Not Found" response.

        * If the user whose profile image is being uploaded exists, but the
          requesting user does not have staff access, the request returns an
          HTTP 404 "Not Found" response.

        * If the specified user exists, and the requesting user has staff
          access, the request returns an HTTP 403 "Forbidden" response.

    **Example DELETE Responses**

        When the requesting user attempts to remove the profile image for
        their own account, the request returns one of the following
        responses:

        * If the image could not be removed, the request returns an HTTP 400
          "Bad Request" response with information about why the request failed.

        * If the request successfully removes the image, the request returns
          an HTTP 204 "No Content" response with no additional content.

        When the requesting user tries to remove the profile image for a
        different user, the view will return one of the following responses:

        * If the requesting user has staff access, and the "username" parameter
          matches a user, the profile image for the specified user is deleted,
          and the request returns an HTTP 204 "No Content" response with no
          additional content.

        * If the requesting user has staff access, but no user is matched by
          the "username" parameter, the request returns an HTTP 404 "Not Found"
          response.

        * If the requesting user does not have staff access, the request
          returns an HTTP 404 "Not Found" response, regardless of whether
          the user exists or not.
    """

    parser_classes = (MultiPartParser, FormParser, TypedFileUploadParser)
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAuthenticated, IsUserInUrl)

    upload_media_types = set(itertools.chain(*(image_type.mimetypes for image_type in IMAGE_TYPES.values())))

    def post(self, request, username):
        """
        POST /api/user/v1/accounts/{username}/image
        """

        # validate request:
        # verify that the user's
        # ensure any file was sent
        if 'file' not in request.FILES:
            return Response(
                {
                    "developer_message": u"No file provided for profile image",
                    "user_message": _(u"No file provided for profile image"),

                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # process the upload.
        uploaded_file = request.FILES['file']

        # no matter what happens, delete the temporary file when we're done
        with closing(uploaded_file):

            # image file validation.
            try:
                validate_uploaded_image(uploaded_file)
            except ImageValidationError as error:
                return Response(
                    {"developer_message": text_type(error), "user_message": error.user_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # generate profile pic and thumbnails and store them
            profile_image_names = get_profile_image_names(username)
            create_profile_images(uploaded_file, profile_image_names)

            # update the user account to reflect that a profile image is available.
            set_has_profile_image(username, True, _make_upload_dt())

            log.info(
                LOG_MESSAGE_CREATE,
                {'image_names': list(profile_image_names.values()), 'user_id': request.user.id}
            )

        # send client response.
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, username):
        """
        DELETE /api/user/v1/accounts/{username}/image
        """

        try:
            # update the user account to reflect that the images were removed.
            set_has_profile_image(username, False)

            # remove physical files from storage.
            profile_image_names = get_profile_image_names(username)
            remove_profile_images(profile_image_names)

            log.info(
                LOG_MESSAGE_DELETE,
                {'image_names': list(profile_image_names.values()), 'user_id': request.user.id}
            )
        except UserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # send client response.
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post64(self, request, username):
        if 'image' not in request.POST:
            return Response(
                {
                    "message": "No file provided for profile image",
                    "status": False,
                    "result": {},
                    "status_code": 400
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # process the upload.
        uploaded_file = request.POST['image']
        # generate profile pic and thumbnails and store them
        create_base64_profile_images(uploaded_file, username)
        # update the user account to reflect that a profile image is available.
        set_has_profile_image(username, True, _make_upload_dt())
        # send client response.
        return Response({"message": "Profile uploaded successfully.","status": True,"result": {},"status_code": 200 })

class ProfileImageUploadView(APIView):
    """
    **DEPRECATION WARNING**

        /api/profile_images/v1/{username}/upload is deprecated.
        All requests should now be sent to
        /api/user/v1/accounts/{username}/image
    """

    parser_classes = ProfileImageView.parser_classes
    authentication_classes = ProfileImageView.authentication_classes
    permission_classes = ProfileImageView.permission_classes

    def post(self, request, username):
        """
        POST /api/profile_images/v1/{username}/upload
        """
        return ProfileImageView().post(request, username)


class ProfileImageRemoveView(APIView):
    """
    **DEPRECATION WARNING**

        /api/profile_images/v1/{username}/remove is deprecated.
        This endpoint's POST is replaced by the DELETE method at
        /api/user/v1/accounts/{username}/image.
    """

    authentication_classes = ProfileImageView.authentication_classes
    permission_classes = ProfileImageView.permission_classes

    def post(self, request, username):
        """
        POST /api/profile_images/v1/{username}/remove
        """
        return ProfileImageView().delete(request, username)


class Base64ImageUpload(APIView):

    authentication_classes = ProfileImageView.authentication_classes
    permission_classes = ProfileImageView.permission_classes

    def post(self, request, username):
        return ProfileImageView().post64(request, username)

