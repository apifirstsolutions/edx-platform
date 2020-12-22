""" API v1 serializers. """


from datetime import datetime

import pytz
import six
from django.utils.translation import ugettext as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import serializers

from course_modes.models import CourseMode
from xmodule.modulestore.django import modulestore

from .models import UNDEFINED, Course


class CourseModeSerializer(serializers.ModelSerializer):
    """ CourseMode serializer. """
    name = serializers.CharField(source='mode_slug')
    price = serializers.IntegerField(source='min_price')
    expires = serializers.DateTimeField(
        source='expiration_datetime',
        required=False,
        allow_null=True,
        format=None
    )

    def get_identity(self, data):
        try:
            return data.get('name', None)
        except AttributeError:
            return None

    class Meta(object):
        model = CourseMode
        fields = ('name', 'currency', 'price', 'sku', 'bulk_sku', 'expires')
        # For disambiguating within the drf-yasg swagger schema
        ref_name = 'commerce.CourseMode'


def validate_course_id(course_id):
    """
    Check that course id is valid and exists in modulestore.
    """
    try:
        course_key = CourseKey.from_string(six.text_type(course_id))
    except InvalidKeyError:
        raise serializers.ValidationError(
            _(u"{course_id} is not a valid course key.").format(
                course_id=course_id
            )
        )

    if not modulestore().has_course(course_key):
        raise serializers.ValidationError(
            _(u'Course {course_id} does not exist.').format(
                course_id=course_id
            )
        )


class PossiblyUndefinedDateTimeField(serializers.DateTimeField):
    """
    We need a DateTime serializer that can deal with the non-JSON-serializable
    UNDEFINED object.
    """
    def to_representation(self, value):
        if value is UNDEFINED:
            return None
        return super(PossiblyUndefinedDateTimeField, self).to_representation(value)


class CourseSerializer(serializers.Serializer):
    """ Course serializer. """
    id = serializers.CharField(validators=[validate_course_id])  # pylint: disable=invalid-name
    name = serializers.CharField(read_only=True)
    difficulty_level = serializers.CharField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    enrollments_count = serializers.IntegerField(read_only=True)
    created = serializers.DateTimeField(read_only=True)
    ratings = serializers.FloatField(required=False)
    verification_deadline = PossiblyUndefinedDateTimeField(format=None, allow_null=True, required=False)
    modes = CourseModeSerializer(many=True)
    discount_applicable = serializers.CharField(required=False)
    discounted_price = serializers.FloatField(required=False)
    sale_type = serializers.CharField(required=False)
    subcategory_id = serializers.CharField(required=False)
    platform_visibility = serializers.CharField(required=False)
    is_premium = serializers.BooleanField(required=False)



    class Meta(object):
        # For disambiguating within the drf-yasg swagger schema
        ref_name = 'commerce.Course'

    def validate(self, attrs):
        """ Ensure the verification deadline occurs AFTER the course mode enrollment deadlines. """
        verification_deadline = attrs.get('verification_deadline', None)

        if verification_deadline:
            upgrade_deadline = None

            # Find the earliest upgrade deadline
            for mode in attrs['modes']:
                expires = mode.get("expiration_datetime")
                if expires:
                    # If we don't already have an upgrade_deadline value, use datetime.max so that we can actually
                    # complete the comparison.
                    upgrade_deadline = min(expires, upgrade_deadline or datetime.max.replace(tzinfo=pytz.utc))

            # In cases where upgrade_deadline is None (e.g. the verified professional mode), allow a verification
            # deadline to be set anyway.
            if upgrade_deadline is not None and verification_deadline < upgrade_deadline:
                raise serializers.ValidationError(
                    'Verification deadline must be after the course mode upgrade deadlines.')

        return attrs

    def create(self, validated_data):
        """
        Create course modes for a course.

        arguments:
            validated_data: The result of self.validate() - a dictionary containing 'id', 'modes', and optionally
            a 'verification_deadline` key.
        returns:
            A ``commerce.api.v1.models.Course`` object.
        """
        kwargs = {}
        if 'verification_deadline' in validated_data:
            kwargs['verification_deadline'] = validated_data['verification_deadline']

        course = Course(
            validated_data["id"],
            self._new_course_mode_models(validated_data["modes"]),
            **kwargs
        )
        course.save()
        return course

    def update(self, instance, validated_data):
        """Update course modes for an existing course. """
        validated_data["modes"] = self._new_course_mode_models(validated_data["modes"])

        instance.update(validated_data)
        instance.save()
        return instance

    @staticmethod
    def _new_course_mode_models(modes_data):
        """Convert validated course mode data to CourseMode objects. """
        return [
            CourseMode(**modes_dict)
            for modes_dict in modes_data
        ]
