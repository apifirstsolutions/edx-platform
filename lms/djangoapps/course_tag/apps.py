from django.apps import AppConfig


class CourseTagConfig(AppConfig):
    name = 'lms.djangoapps.course_tag'
    verbose_name = 'course_tag'

    def ready(self):
        from django.db.models import CharField
        from django.db.models.functions import Lower

        CharField.register_lookup(Lower)
