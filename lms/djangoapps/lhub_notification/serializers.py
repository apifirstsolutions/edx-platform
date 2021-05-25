from django.urls import reverse
from rest_framework import serializers
from lms.djangoapps.lhub_notification.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    num_new_notifications = serializers.SerializerMethodField()
    course_url = serializers.SerializerMethodField()
    course_id = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'course_url', 'num_new_notifications',
                  'notification_type', 'created', 'days_warning', 'course_id']
        read_only_fields = ('title', 'message', 'notification_type', 'created', 'days_warning')

    def get_course_url(self, obj):
        return reverse('course_root', kwargs={'course_id': obj.course_id}) if obj.course else ''

    def get_num_new_notifications(self, obj):
        return obj.num_new_notifications

    def get_course_id(self, obj):
        return str(obj.course_id)
