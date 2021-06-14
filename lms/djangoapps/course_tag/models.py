
# Create your models here.
from django.db import models
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from django.contrib.auth.models import User


# Create your models here.
class CourseTagType(models.Model):
    PLATFORM_CHOICES = (('mobile', 'MOBILE'), ('web', 'WEB'), ('both', 'BOTH'))
    name = models.CharField(max_length=255, null= False, blank=False)
    display_name = models.CharField(max_length=255, null= False, blank=False)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    is_enabled = models.BooleanField(default=True)
    sector = models.CharField(max_length=255, null=True, blank=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, )
    sequence = models.IntegerField(blank=True, default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name

class CourseTag(models.Model):
    course_tag_type = models.ForeignKey(CourseTagType, related_name = 'course_tag_type', on_delete=models.CASCADE)
    course_over_view = models.ForeignKey(CourseOverview, related_name='crs_ovr_view', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)






