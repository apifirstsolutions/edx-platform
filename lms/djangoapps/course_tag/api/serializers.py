"""
Serializers for Course Tag
"""
from rest_framework import serializers
from lms.djangoapps.course_tag.models import CourseTagType, CourseTag
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from logging import getLogger

log = getLogger(__name__)


class CourseTagTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for CourseTagType
    """

    class Meta(object):
        model = CourseTagType
        fields= ('id', 'display_name', 'is_enabled', 'platform')
