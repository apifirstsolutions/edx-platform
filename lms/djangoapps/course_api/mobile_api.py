"""
Course API
"""
import logging

from edx_when.api import get_dates_for_course
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied
import search
import six
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.courses import (
    get_course_overview_with_access,
    get_courses,
    get_courses_with_extra_info_json,
    get_permission_for_course_about
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.view_utils import LazySequence
from student.roles import GlobalStaff
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from .permissions import can_view_courses_for_username


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


UNKNOWN_BLOCK_DISPLAY_NAME = 'UNKNOWN'


def get_effective_user(requesting_user, target_username):
    """
    Get the user we want to view information on behalf of.
    """
    if target_username == requesting_user.username:
        return requesting_user
    elif target_username == '':
        return AnonymousUser()
    elif can_view_courses_for_username(requesting_user, target_username):
        return User.objects.get(username=target_username)
    else:
        raise PermissionDenied()


def course_detail(request, username, course_key):
    """
    Return a single course identified by `course_key`.

    The course must be visible to the user identified by `username` and the
    logged-in user should have permission to view courses available to that
    user.

    Arguments:
        request (HTTPRequest):
            Used to identify the logged-in user and to instantiate the course
            module to retrieve the course about description
        username (string):
            The name of the user `requesting_user would like to be identified as.
        course_key (CourseKey): Identifies the course of interest

    Return value:
        `CourseOverview` object representing the requested course
    """
    user = get_effective_user(request.user, username)
    overview = get_course_overview_with_access(
        user,
        get_permission_for_course_about(),
        course_key,
    )
    overview.effective_user = user
    return overview


def _filter_by_search(course_queryset, search_term):
    """
    Filters a course queryset by the specified search term.
    """
    if not settings.FEATURES['ENABLE_COURSEWARE_SEARCH'] or not search_term:
        return course_queryset

    # Return all the results, 10K is the maximum allowed value for ElasticSearch.
    # We should use 0 after upgrading to 1.1+:
    #   - https://github.com/elastic/elasticsearch/commit/8b0a863d427b4ebcbcfb1dcd69c996c52e7ae05e
    results_size_infinity = 10000

    search_courses = search.api.course_discovery_search(
        search_term,
        size=results_size_infinity,
    )

    search_courses_ids = {course['data']['id'] for course in search_courses['results']}

    return LazySequence(
        (
            course for course in course_queryset
            if six.text_type(course.id) in search_courses_ids
        ),
        est_len=len(course_queryset)
    )


def list_courses(request, username, org=None, platform=None, filter_=None, search_term=None, get_extra_info=False):
    """
    Yield all available courses.

    The courses returned are all be visible to the user identified by
    `username` and the logged in user should have permission to view courses
    available to that user.

    Arguments:
        request (HTTPRequest):
            Used to identify the logged-in user and to instantiate the course
            module to retrieve the course about description
        username (string):
            The name of the user the logged-in user would like to be
            identified as

    Keyword Arguments:
        org (string):
            If specified, visible `CourseOverview` objects are filtered
            such that only those belonging to the organization with the provided
            org code (e.g., "HarvardX") are returned. Case-insensitive.
        filter_ (dict):
            If specified, visible `CourseOverview` objects are filtered
            by the given key-value pairs.
        search_term (string):
            Search term to filter courses (used by ElasticSearch).

    Return value:
        Yield `CourseOverview` objects representing the collection of courses.
    """
    user = get_effective_user(request.user, username)
    if get_extra_info:
        course_qs = get_courses_with_extra_info_json(user, org=org, platform=platform, filter_=filter_)
    else:
        course_qs = get_courses(user, org=org, platform=platform, filter_=filter_)
    course_qs = _filter_by_search(course_qs, search_term)
    return course_qs


def list_course_keys(request, username, role):
    """
    Yield all available CourseKeys for the user having the given role.

    The courses returned include those for which the user identified by
    `username` has the given role.  Additionally, the logged in user
    should have permission to view courses available to that user.

    Note: This function does not use branding to determine courses.

    Arguments:
        request (HTTPRequest):
            Used to identify the logged-in user and to instantiate the course
            module to retrieve the course about description
        username (string):
            The name of the user the logged-in user would like to be
            identified as

    Keyword Arguments:
        role (string):
            Course keys are filtered such that only those for which the
            user has the specified role are returned.

    Return value:
        Yield `CourseKey` objects representing the collection of courses.

    """
    user = get_effective_user(request.user, username)

    course_keys = CourseOverview.get_all_course_keys()

    # Global staff have access to all courses. Filter courses for non-global staff.
    if GlobalStaff().has_user(user):
        return course_keys

    return LazySequence(
        (
            course_key for course_key in course_keys
            if has_access(user, role, course_key)
        ),
        est_len=len(course_keys)
    )


def get_due_dates(request, course_key, user):
    """
    Get due date information for a user for blocks in a course.

    Arguments:
        request: the request object
        course_key (CourseKey): the CourseKey for the course
        user: the user object for which we want due date information

    Returns:
        due_dates (list): a list of dictionaries containing due date information
            keys:
                name: the display name of the block
                url: the deep link to the block
                date: the due date for the block
    """
    dates = get_dates_for_course(
        course_key,
        user,
    )

    store = modulestore()

    due_dates = []
    for (block_key, date_type), date in six.iteritems(dates):
        if date_type == 'due':
            try:
                block_display_name = store.get_item(block_key).display_name
            except ItemNotFoundError:
                logger.exception('Failed to get block for due date item with key: {}'.format(block_key))
                block_display_name = UNKNOWN_BLOCK_DISPLAY_NAME

            # get url to the block in the course
            block_url = reverse('jump_to', args=[course_key, block_key])
            block_url = request.build_absolute_uri(block_url)

            due_dates.append({
                'name': block_display_name,
                'url': block_url,
                'date': date,
            })
    return due_dates


def get_course_run_url(request, course_id):
    """
    Get the URL to a course run.

    Arguments:
        request: the request object
        course_id (string): the course id of the course

    Returns:
        (string): the URL to the course run associated with course_id
    """
    course_run_url = reverse('openedx.course_experience.course_home', args=[course_id])
    return request.build_absolute_uri(course_run_url)









import logging

from common.djangoapps.course_modes.models import CourseMode
from django.core.exceptions import ObjectDoesNotExist, ValidationError  # lint-amnesty, pylint: disable=wrong-import-order
from django.utils.decorators import method_decorator  # lint-amnesty, pylint: disable=wrong-import-order
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication  # lint-amnesty, pylint: disable=wrong-import-order
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser  # lint-amnesty, pylint: disable=wrong-import-order
from opaque_keys import InvalidKeyError  # lint-amnesty, pylint: disable=wrong-import-order
from opaque_keys.edx.keys import CourseKey  # lint-amnesty, pylint: disable=wrong-import-order
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.core.djangoapps.cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from openedx.core.djangoapps.course_groups.cohorts import CourseUserGroup, add_user_to_cohort, get_cohort_by_name
from openedx.core.djangoapps.embargo import api as embargo_api
from openedx.core.djangoapps.enrollments import api
from openedx.core.djangoapps.enrollments.errors import (
    CourseEnrollmentError, CourseEnrollmentExistsError, CourseModeNotFoundError,
)

from openedx.core.djangoapps.enrollments.forms import CourseEnrollmentsApiListForm
from openedx.core.djangoapps.enrollments.paginators import CourseEnrollmentsApiListPagination
from openedx.core.djangoapps.enrollments.serializers import CourseEnrollmentsApiListSerializer
from openedx.core.djangoapps.user_api.accounts.permissions import CanRetireUser
from openedx.core.djangoapps.user_api.models import UserRetirementStatus
from openedx.core.djangoapps.user_api.preferences.api import update_email_opt_in
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission, ApiKeyHeaderPermissionIsAuthenticated
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from openedx.core.lib.exceptions import CourseNotFoundError
from openedx.core.lib.log_utils import audit_log
from openedx.features.enterprise_support.api import (
    ConsentApiServiceClient,
    EnterpriseApiException,
    EnterpriseApiServiceClient,
    enterprise_enabled
)
from rest_framework import permissions, status  # lint-amnesty, pylint: disable=wrong-import-order
from rest_framework.generics import ListAPIView  # lint-amnesty, pylint: disable=wrong-import-order
from rest_framework.response import Response  # lint-amnesty, pylint: disable=wrong-import-order
from rest_framework.throttling import UserRateThrottle  # lint-amnesty, pylint: disable=wrong-import-order
from rest_framework.views import APIView  # lint-amnesty, pylint: disable=wrong-import-order
from common.djangoapps.student.auth import user_has_role
from common.djangoapps.student.models import CourseEnrollment, User
from common.djangoapps.student.roles import CourseStaffRole, GlobalStaff
from common.djangoapps.util.disable_rate_limit import can_disable_rate_limit
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from openedx.core.lib.api.authentication import BearerAuthentication
from rest_framework.permissions import IsAuthenticated
from common.djangoapps.student.models import CourseEnrollment

log = logging.getLogger(__name__)
REQUIRED_ATTRIBUTES = {
    "credit": ["credit:provider_id"],
}

@api_view(['POST'])
@authentication_classes((BearerAuthenticationAllowInactiveUser,))
@permission_classes((IsAuthenticated,))
def enroll_course_endpoint(request):
    """
    Enrolls the current user to a course.
    Requirments:
    * Course needs to be unpaid
    * Valid course id needs to be provided
    * User needs to be authenticated
    """
    username = request.data.get('user', request.user.username)
    course_id = request.data.get('course_details', {}).get('course_id')

    if not course_id:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data={"message": "Course ID must be specified to create a new enrollment."}
        )

    try:
        course_id = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "message": f"No course '{course_id}' found for enrollment"
            }
        )

    mode = request.data.get('mode')

    # Check that the user specified is either the same user, or this is a server-to-server request.
    if not username:
        username = request.user.username
    if username != request.user.username and not GlobalStaff().has_user(request.user):
        # Return a 404 instead of a 403 (Unauthorized). If one user is looking up
        # other users, do not let them deduce the existence of an enrollment.
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        #enrollment = CourseEnrollment.objects.get(user__username=username, course_id=course_id)
        is_enrolled = CourseEnrollment.is_enrolled(request.user, course_id)
        if is_enrolled:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={ "message": "You are already enrolled." })
    except:
        pass

    if mode not in (CourseMode.AUDIT, CourseMode.HONOR, None) and not GlobalStaff().has_user(request.user):
        return Response(
            status=status.HTTP_403_FORBIDDEN,
            data={
                "message": "User does not have permission to create enrollment with mode [{mode}].".format(
                    mode=mode
                )
            }
        )

    try:
        # Lookup the user, instead of using request.user, since request.user may not match the username POSTed.
        user = User.objects.get(username=username)
    except ObjectDoesNotExist:
        return Response(
            status=status.HTTP_406_NOT_ACCEPTABLE,
            data={
                'message': f'The user {username} does not exist.'
            }
        )

    embargo_response = embargo_api.get_embargo_response(request, course_id, user)

    if embargo_response:
        return embargo_response

    try:
        is_active = request.data.get('is_active')
        # Check if the requested activation status is None or a Boolean
        if is_active is not None and not isinstance(is_active, bool):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'message': ("'{value}' is an invalid enrollment activation status.").format(value=is_active)
                }
            )

        explicit_linked_enterprise = request.data.get('linked_enterprise_customer')
        if explicit_linked_enterprise and ApiKeyHeaderPermission().has_permission(request) and enterprise_enabled():
            enterprise_api_client = EnterpriseApiServiceClient()
            consent_client = ConsentApiServiceClient()
            try:
                enterprise_api_client.post_enterprise_course_enrollment(username, str(course_id), None)
            except EnterpriseApiException as error:
                log.exception("An unexpected error occurred while creating the new EnterpriseCourseEnrollment "
                                "for user [%s] in course run [%s]", username, course_id)
                raise CourseEnrollmentError(str(error))  # lint-amnesty, pylint: disable=raise-missing-from
            kwargs = {
                'username': username,
                'course_id': str(course_id),
                'enterprise_customer_uuid': explicit_linked_enterprise,
            }
            consent_client.provide_consent(**kwargs)

        enrollment_attributes = request.data.get('enrollment_attributes')
        enrollment = api.get_enrollment(username, str(course_id))
        mode_changed = enrollment and mode is not None and enrollment['mode'] != mode
        active_changed = enrollment and is_active is not None and enrollment['is_active'] != is_active
        missing_attrs = []
        if enrollment_attributes:
            actual_attrs = [
                "{namespace}:{name}".format(**attr)
                for attr in enrollment_attributes
            ]
            missing_attrs = set(REQUIRED_ATTRIBUTES.get(mode, [])) - set(actual_attrs)
        if GlobalStaff().has_user(request.user) and (mode_changed or active_changed):
            if mode_changed and active_changed and not is_active:
                # if the requester wanted to deactivate but specified the wrong mode, fail
                # the request (on the assumption that the requester had outdated information
                # about the currently active enrollment).
                msg = "Enrollment mode mismatch: active mode={}, requested mode={}. Won't deactivate.".format(
                    enrollment["mode"], mode
                )
                log.warning(msg)
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": msg})

            if missing_attrs:
                msg = "Missing enrollment attributes: requested mode={} required attributes={}".format(
                    mode, REQUIRED_ATTRIBUTES.get(mode)
                )
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": msg})

            response = api.update_enrollment(
                username,
                str(course_id),
                mode=mode,
                is_active=is_active,
                enrollment_attributes=enrollment_attributes,
                # If we are updating enrollment by authorized api caller, we should allow expired modes
            )
        else:
            # Will reactivate inactive enrollments.
            response = api.add_enrollment(
                username,
                str(course_id),
                mode=mode,
                is_active=is_active,
                enrollment_attributes=enrollment_attributes
            )

        cohort_name = request.data.get('cohort')
        if cohort_name is not None:
            cohort = get_cohort_by_name(course_id, cohort_name)
            try:
                add_user_to_cohort(cohort, user)
            except ValueError:
                # user already in cohort, probably because they were un-enrolled and re-enrolled
                log.exception('Cohort re-addition')
        email_opt_in = request.data.get('email_opt_in', None)
        if email_opt_in is not None:
            org = course_id.org
            update_email_opt_in(request.user, org, email_opt_in)

        log.info('The user [%s] has already been enrolled in course run [%s].', username, course_id)
        return Response(response)
    except CourseModeNotFoundError as error:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "message": (
                    "The course is not free or has been expired."
                ).format(mode=mode, course_id=course_id),
            })
    except CourseNotFoundError:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "message": f"No course '{course_id}' found for enrollment"
            }
        )
    except CourseEnrollmentExistsError as error:
        log.warning('An enrollment already exists for user [%s] in course run [%s].', username, course_id)
        return Response(data=error.enrollment)
    except CourseEnrollmentError:
        log.exception("An error occurred while creating the new course enrollment for user "
                        "[%s] in course run [%s]", username, course_id)
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "message": (
                    "An error occurred while creating the new course enrollment for user "
                    "'{username}' in course '{course_id}'"
                ).format(username=username, course_id=course_id)
            }
        )
    except CourseUserGroup.DoesNotExist:
        log.exception('Missing cohort [%s] in course run [%s]', cohort_name, course_id)
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "message": "An error occured while adding to cohort [%s]" % cohort_name
            })
    finally:
        # Assumes that the ecommerce service uses an API key to authenticate.
        current_enrollment = api.get_enrollment(username, str(course_id))
        audit_log(
            'enrollment_change_requested',
            course_id=str(course_id),
            requested_mode=mode,
            actual_mode=current_enrollment['mode'] if current_enrollment else None,
            requested_activation=is_active,
            actual_activation=current_enrollment['is_active'] if current_enrollment else None,
            user_id=user.id
        )

