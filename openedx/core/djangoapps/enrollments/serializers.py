"""
Serializers for all Course Enrollment related return objects.
"""

import logging

from rest_framework import serializers
from openedx.core.lib.api.fields import AbsoluteURLField
from course_modes.models import CourseMode
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore
from lms.djangoapps.course_api.blocks.api import get_blocks
from lms.djangoapps.courseware.module_render import get_module, get_module_by_usage_id, get_module_for_descriptor
from lms.djangoapps.courseware.courses import get_course_with_access
from opaque_keys.edx.keys import CourseKey, UsageKey
from six import iteritems, text_type
from completion.models import BlockCompletion
from datetime import date, timedelta
import itertools

from common.djangoapps.student.views.dashboard import (
    get_org_black_and_whitelist_for_site,
    get_course_enrollments,
    get_dashboard_course_limit,
    get_filtered_course_entitlements,
)

log = logging.getLogger(__name__)


class StringListField(serializers.CharField):
    """Custom Serializer for turning a comma delimited string into a list.

    This field is designed to take a string such as "1,2,3" and turn it into an actual list
    [1,2,3]

    """

    def field_to_native(self, obj, field_name):  # pylint: disable=unused-argument
        """
        Serialize the object's class name.
        """
        if not obj.suggested_prices:
            return []

        items = obj.suggested_prices.split(',')
        return [int(item) for item in items]


class _MediaSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a media object.
    """

    def __init__(self, uri_attribute, *args, **kwargs):
        super(_MediaSerializer, self).__init__(*args, **kwargs)
        self.uri_attribute = uri_attribute

    uri = serializers.SerializerMethodField(source='*')

    def get_uri(self, course_overview):
        """
        Get the representation for the media resource's URI
        """
        return getattr(course_overview, self.uri_attribute)


class _CourseApiMediaCollectionSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a collection of media objects
    """
    course_image = _MediaSerializer(source='*', uri_attribute='course_image_url')


class MobileCourseSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serialize a course descriptor and related information.
    """

    course_id = serializers.CharField(source="id")
    course_name = serializers.CharField(source="display_name_with_default")
    enrollment_start = serializers.DateTimeField(format=None)
    enrollment_end = serializers.DateTimeField(format=None)
    course_start = serializers.DateTimeField(source="start", format=None)
    course_end = serializers.DateTimeField(source="end", format=None)
    invite_only = serializers.BooleanField(source="invitation_only")
    course_modes = serializers.SerializerMethodField()
    media = _CourseApiMediaCollectionSerializer(source='*')
    total_units = serializers.SerializerMethodField()
    completed_units = serializers.SerializerMethodField()

    class Meta(object):
        # For disambiguating within the drf-yasg swagger schema
        ref_name = 'enrollment.Course'

    def __init__(self, *args, **kwargs):
        self.include_expired = kwargs.pop("include_expired", False)
        super(MobileCourseSerializer, self).__init__(*args, **kwargs)

    def get_total_units(self, instance):
        request = self.context.get('request', None)
        user = request.user
        course_usage_key = modulestore().make_course_usage_key(instance.id)
        response = get_blocks(request, course_usage_key, user, requested_fields=['completion'],
                              block_types_filter='vertical')
        total_units = len(response['blocks'])
        return total_units

    def get_completed_units(self, instance):
        request = self.context.get('request', None)
        user = request.user
        course_usage_key = modulestore().make_course_usage_key(instance.id)
        response = get_blocks(request, course_usage_key, user, requested_fields=['completion'],
                              block_types_filter='vertical')
        completed_units = 0
        for key, block in response['blocks'].items():
            usage_key = UsageKey.from_string(block['id'])
            usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
            course_key = usage_key.course_key
            course = instance
            block, _ = get_module_by_usage_id(
                request, text_type(course_key), text_type(usage_key), disable_staff_debug_info=True, course=course
            )
            completion_service = block.runtime.service(block, 'completion')
            complete = completion_service.vertical_is_complete(block)
            if complete:
                completed_units += 1
        return completed_units

    def get_course_modes(self, obj):
        """
        Retrieve course modes associated with the course.
        """
        course_modes = CourseMode.modes_for_course(
            obj.id,
            include_expired=self.include_expired,
            only_selectable=False
        )
        return [
            ModeSerializer(mode).data
            for mode in course_modes
        ]


class CourseSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serialize a course descriptor and related information.
    """

    course_id = serializers.CharField(source="id")
    course_name = serializers.CharField(source="display_name_with_default")
    enrollment_start = serializers.DateTimeField(format=None)
    enrollment_end = serializers.DateTimeField(format=None)
    course_start = serializers.DateTimeField(source="start", format=None)
    course_end = serializers.DateTimeField(source="end", format=None)
    invite_only = serializers.BooleanField(source="invitation_only")
    course_modes = serializers.SerializerMethodField()

    class Meta(object):
        # For disambiguating within the drf-yasg swagger schema
        ref_name = 'enrollment.Course'

    def __init__(self, *args, **kwargs):
        self.include_expired = kwargs.pop("include_expired", False)
        super(CourseSerializer, self).__init__(*args, **kwargs)

    def get_course_modes(self, obj):
        """
        Retrieve course modes associated with the course.
        """
        course_modes = CourseMode.modes_for_course(
            obj.id,
            include_expired=self.include_expired,
            only_selectable=False
        )
        return [
            ModeSerializer(mode).data
            for mode in course_modes
        ]


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializes CourseEnrollment models

    Aggregates all data from the Course Enrollment table, and pulls in the serialization for
    the Course Descriptor and course modes, to give a complete representation of course enrollment.

    """
    course_details = CourseSerializer(source="course_overview")
    user = serializers.SerializerMethodField('get_username')

    def get_username(self, model):
        """Retrieves the username from the associated model."""
        return model.username

    class Meta(object):
        model = CourseEnrollment
        fields = ('created', 'mode', 'is_active', 'course_details', 'user')
        lookup_field = 'username'


class CourseEnrollmentsApiListSerializer(CourseEnrollmentSerializer):
    """
    Serializes CourseEnrollment model and returns a subset of fields returned
    by the CourseEnrollmentSerializer.
    """
    course_id = serializers.CharField(source='course_overview.id')

    def __init__(self, *args, **kwargs):
        super(CourseEnrollmentsApiListSerializer, self).__init__(*args, **kwargs)
        self.fields.pop('course_details')

    class Meta(CourseEnrollmentSerializer.Meta):
        fields = CourseEnrollmentSerializer.Meta.fields + ('course_id',)


class ModeSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializes a course's 'Mode' tuples

    Returns a serialized representation of the modes available for course enrollment. The course
    modes models are designed to return a tuple instead of the model object itself. This serializer
    does not handle the model object itself, but the tuple.

    """
    slug = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    min_price = serializers.IntegerField()
    suggested_prices = StringListField(max_length=255)
    currency = serializers.CharField(max_length=8)
    expiration_datetime = serializers.DateTimeField()
    description = serializers.CharField()
    sku = serializers.CharField()
    bulk_sku = serializers.CharField()


class ImageSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Collection of URLs pointing to images of various sizes.

    The URLs will be absolute URLs with the host set to the host of the current request. If the values to be
    serialized are already absolute URLs, they will be unchanged.
    """
    raw = AbsoluteURLField()
    small = AbsoluteURLField()
    large = AbsoluteURLField()


class _CourseApiMediaCollectionSerializer1(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a collection of media objects
    """
    course_image = _MediaSerializer(source='*', uri_attribute='course_image_url')


class MobileCourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializes CourseEnrollment models

    Aggregates all data from the Course Enrollment table, and pulls in the serialization for
    the Course Descriptor and course modes, to give a complete representation of course enrollment.

    """
    course_details = MobileCourseSerializer(source="course_overview")
    user = serializers.SerializerMethodField('get_username')

    # media = _CourseApiMediaCollectionSerializer(source='*')

    def get_username(self, model):
        """Retrieves the username from the associated model."""
        return model.username

    class Meta(object):
        model = CourseEnrollment
        fields = ('created', 'mode', 'is_active', 'course_details', 'user')
        lookup_field = 'username'


class LearnerProgressSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    course_details = serializers.SerializerMethodField()
    ten_days_progress_data = serializers.SerializerMethodField()
    sub_units_completed_today = serializers.SerializerMethodField()

    class Meta:
        model = BlockCompletion
        fields = ['user', 'course_details', 'ten_days_progress_data', 'sub_units_completed_today']

    def get_user(self, instance):
        request = self.context.get('request', None)
        user = request.user
        return user.id

    def get_course_details(self, instance):
        request = self.context.get('request', None)
        user = request.user

        courses_completed = []
        in_progress_courses = []
        units_completed = 0
        units_total = 0

        course_enrollments = get_course_enrollment(request, user)
        courses = {}
        for i, course in enumerate(course_enrollments):
            units_completed += course.completed_units
            units_total += course.total_units

            if course.completed_units == course.total_units:
                courses_completed.append(course)
            else:
                in_progress_courses.append(course)
                # if course.total_units != 0:
                #     courses[str(course.course_id)] = round(float(course.completed_units) / float(course.total_units) * 100, 2)
                # else:
                #     courses[str(course.course_id)] = 0

        num_of_in_progress_courses = len(in_progress_courses)
        num_of_courses_completed = len(courses_completed)
        total_courses = num_of_in_progress_courses + num_of_courses_completed
        avg_course_completion = 0
        if not num_of_courses_completed == 0:
            avg_course_completion = round(float(num_of_courses_completed) / float(total_courses) * 100, 2)

        # sliced_ten_course_progress = dict(itertools.islice(courses.items(), 10))

        content = {
            'course_in_progress': num_of_in_progress_courses,
            'course_completed': num_of_courses_completed,
            'average_course_completion': str(avg_course_completion),
            'units_completed': units_completed,
            'units_total': units_total,
            # 'course_progress_rate': sliced_ten_course_progress,
        }

        return content

    def get_ten_days_progress_data(self, instance):
        request = self.context.get('request', None)
        user = request.user

        valid = []
        today = date.today()
        for i in range(10):
            past_ten = today - timedelta(i)
            to_date = past_ten + timedelta(1)

            qset = BlockCompletion.objects.filter(
                user=user,
                modified__gte=past_ten,
                modified__lt=to_date,
            )

            completed = qset.count()
            dateStr = past_ten.strftime("%d-%m-%Y")
            valid.append({'date': dateStr, 'count': completed})
            # valid[dateStr] = (completed)

        return valid

    def get_sub_units_completed_today(self, instance):
        request = self.context.get('request', None)
        user = request.user

        today = date.today()
        block_completions = BlockCompletion.objects.filter(
            user=user,
            modified__gte=today,
        )
        today_completed = block_completions.count()
        return today_completed


def get_units_and_block_ids(request, instance, date):
    user = request.user
    course_usage_key = modulestore().make_course_usage_key(instance)
    response = get_blocks(request, course_usage_key, user, requested_fields=['completion'],
                          block_types_filter='vertical')
    blk = {}
    completed_units = 0

    for key, block in response['blocks'].items():
        usage_key = UsageKey.from_string(block['id'])
        usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
        course_key = usage_key.course_key
        course = instance
        block, _ = get_module_by_usage_id(
            request, text_type(course_key), text_type(usage_key), disable_staff_debug_info=True
        )

        completion_service = block.runtime.service(block, 'completion')
        complete = completion_service.vertical_is_complete(block)
        if complete:
            # blk[str(usage_key)] = [str(b) for b in block.children]
            completed_units += 1

    return completed_units


def get_course_enrollment(request, user):
    disable_course_limit = request and 'course_limit' in request.GET
    course_limit = get_dashboard_course_limit() if not disable_course_limit else None

    # Get the org whitelist or the org blacklist for the current site
    site_org_whitelist, site_org_blacklist = get_org_black_and_whitelist_for_site()
    course_enrollments = list(
        get_course_enrollments(user, site_org_whitelist, site_org_blacklist, course_limit, request=request))

    # Get the entitlements for the user and a mapping to all available sessions for that entitlement
    # If an entitlement has no available sessions, pass through a mock course overview object
    (course_entitlements,
     course_entitlement_available_sessions,
     unfulfilled_entitlement_pseudo_sessions) = get_filtered_course_entitlements(
        user,
        site_org_whitelist,
        site_org_blacklist
    )

    # Sort the enrollment pairs by the enrollment date
    course_enrollments.sort(key=lambda x: x.created, reverse=True)

    # Filter out any course enrollment course cards that are associated with fulfilled entitlements
    for entitlement in [e for e in course_entitlements if e.enrollment_course_run is not None]:
        course_enrollments = [
            enr for enr in course_enrollments if entitlement.enrollment_course_run.course_id != enr.course_id
        ]

    web_course_enrollments = []
    for course in course_enrollments:
        platform = course._course_overview.platform_visibility
        if platform in [None, 'Mobile', 'Both']:
            web_course_enrollments.append(course)

    return course_entitlements + web_course_enrollments
