import logging

import edx_api_doc_tools as apidocs
import six
from django.contrib.auth import get_user_model
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.response import Response

from lms.djangoapps.certificates.api import get_certificate_for_user, get_certificates_for_user
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from lms.djangoapps.certificates.apis.v0.views import CertificatesDetailView, CertificatesListView


log = logging.getLogger(__name__)
User = get_user_model()


class LHUBCertificatesDetailView(CertificatesDetailView):

    def get(self, request, username, course_id):
        """
        Gets a certificate information.

        Args:
            request (Request): Django request object.
            username (string): URI element specifying the user's username.
            course_id (string): URI element specifying the course location.

        Return:
            A JSON serialized representation of the certificate.
        """
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.warning(u'Course ID string "%s" is not valid', course_id)
            return Response(
                status=404,
                data={
                    "message": "course_id_not_valid",
                    "status": False,
                    "status_code": 404,
                    "result": {}
                }
            )

        user_cert = get_certificate_for_user(username=username, course_key=course_key)
        if user_cert is None:
            return Response(
                status=404,
                data={
                    "message": "no_certificate_for_user",
                    "status": False,
                    "status_code": 404,
                    "result": {}
                }
            )

        course_overview = CourseOverview.get_from_id(course_id)
        # return 404 if it's not a PDF certificates and there is no active certificate configuration.
        if not user_cert['is_pdf_certificate'] and not course_overview.has_any_active_web_certificate:
            return Response(
                status=404,
                data={
                    "message": "no_certificate_configuration_for_course",
                    "status": False,
                    "status_code": 404,
                    "result": {}
                }
            )

        return Response(
            {
                "message": "",
                "status": True,
                "status_code": 200,
                "result": {
                    "username": user_cert.get('username'),
                    "course_id": six.text_type(user_cert.get('course_key')),
                    "certificate_type": user_cert.get('type'),
                    "created_date": user_cert.get('created'),
                    "status": user_cert.get('status'),
                    "is_passing": user_cert.get('is_passing'),
                    "download_url": user_cert.get('download_url'),
                    "download_pdf_url": user_cert.get('download_pdf_url'),
                    "grade": user_cert.get('grade')
                }
            }
        )


class LHUBCertificatesListView(CertificatesListView):
    @apidocs.schema(parameters=[
        apidocs.string_parameter(
            'username',
            apidocs.ParameterLocation.PATH,
            description="The users to get certificates for",
        )
    ])
    def get(self, request, username):
        """Get a paginated list of bookmarks for a user.

        **Use Case**

        Get the list of viewable course certificates for a specific user.

        **Example Request**

        GET /api/certificates/v0/certificates/lhub/{username}

        **GET Response Values**

            If the request for information about the user's certificates is successful,
            an HTTP 200 "OK" response is returned.

            The HTTP 200 response contains a list of dicts with the following keys/values.

            * username: A string representation of an user's username passed in the request.

            * course_id: A string representation of a Course ID.

            * course_display_name: A string representation of the Course name.

            * course_organization: A string representation of the organization associated with the Course.

            * certificate_type: A string representation of the certificate type.
                Can be honor|verified|professional

            * created_date: Date/time the certificate was created, in ISO-8661 format.

            * status: A string representation of the certificate status.

            * is_passing: True if the certificate has a passing status, False if not.

            * download_url: A string representation of the certificate url.

            * download_pdf_url: A string representation of path to certificate pdf file

            * grade: A string representation of a float for the user's course grade.

        **Example GET Response**

            {
                "message": "",
                "status": true,
                "status_code": 200,
                "result": [
                    {
                        "username": "edx",
                        "course_id": "course-v1:rg+cr1+cr1",
                        "course_display_name": "Checked reviews",
                        "course_organization": "rg",
                        "certificate_type": "honor",
                        "created_date": "2021-04-07T14:03:44.560960Z",
                        "modified_date": "2021-04-07T14:03:44.628549Z",
                        "status": "downloadable",
                        "is_passing": true,
                        "download_url": "/certificates/08f0e53458da4fbbb734db84d6181980",
                        "download_pdf_url": "/media/certificates_pdf/08f0e53458da4fbbb734db84d6181980",
                        "grade": "1.0"
                    },
                    {
                        "username": "edx",
                        "course_id": "course-v1:rg+q1+q1",
                        "course_display_name": "qwerty",
                        "course_organization": "rg",
                        "certificate_type": "honor",
                        "created_date": "2021-04-07T14:14:59.497563Z",
                        "modified_date": "2021-04-07T14:15:00.162415Z",
                        "status": "downloadable",
                        "is_passing": true,
                        "download_url": "/certificates/9e1b971ec5964f6a9d91bd2388237097",
                        "download_pdf_url": "/media/certificates_pdf/9e1b971ec5964f6a9d91bd2388237097",
                        "grade": "0.0"
                    }
                ]
            }
        """
        user_certs = []
        if self._viewable_by_requestor(request, username):
            for user_cert in self._get_certificates_for_user(username):
                user_certs.append({
                    'username': user_cert.get('username'),
                    'course_id': six.text_type(user_cert.get('course_key')),
                    'course_display_name': user_cert.get('course_display_name'),
                    'course_organization': user_cert.get('course_organization'),
                    'certificate_type': user_cert.get('type'),
                    'created_date': user_cert.get('created'),
                    'modified_date': user_cert.get('modified'),
                    'status': user_cert.get('status'),
                    'is_passing': user_cert.get('is_passing'),
                    'download_url': user_cert.get('download_url'),
                    "download_pdf_url": user_cert.get('download_pdf_url'),
                    'grade': user_cert.get('grade'),
                })
            return Response(
                {
                    "message": "",
                    "status": True,
                    "status_code": 200,
                    "result": user_certs
                }
            )
        return Response(
            {
                "message": "no_certificates_for_user",
                "status": False,
                "status_code": 200,
                "result": user_certs
            }
        )
