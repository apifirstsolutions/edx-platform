"""
Serializers for Course Tag
"""
from rest_framework import serializers
from lms.djangoapps.course_tag.models import CourseTagType, CourseTag
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from logging import getLogger
log = getLogger(__name__)

class CourseTagSerializer(serializers.ModelSerializer):
    """
    Serializer for CourseTag model.
    """

    course_id = serializers.SerializerMethodField('course_id_')
    course_tag_type = serializers.SerializerMethodField('tag_type')
    is_enabled = serializers.SerializerMethodField('check_enabled')
    platform = serializers.SerializerMethodField('platform_')
    def course_id_(self, obj):
        if obj.course_over_view.display_name and obj.course_over_view.display_number_with_default:
            return str(CourseOverview.objects.filter(display_name = obj.course_over_view.display_name, display_number_with_default = obj.course_over_view.display_number_with_default).values_list('id', flat=True)[0])
        else:
            return None
    def tag_type(self, obj):
        if obj:
            return obj.course_tag_type.display_name
        return None
    def check_enabled(self, obj):
        if obj:
            return obj.course_tag_type.is_enabled
        return False
    def platform_(self, obj):
        if obj:
            return obj.course_tag_type.platform

    class Meta(object):
        model = CourseTag
        fields = ('course_id', 'course_tag_type', 'is_enabled', 'platform')

