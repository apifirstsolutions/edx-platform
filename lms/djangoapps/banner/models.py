from django.db import models
# Create your models here.
from django.db import models
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from django.contrib.auth.models import User


# Create your models here.
class Banner(models.Model):
    PLATFORM_CHOICES=(('mobile', 'MOBILE'), ('web', 'WEB'), ('both', 'BOTH'))
    LINK_CHOICES=(('about', 'ABOUT'), ('bundle', 'BUNDLE'), ('subscription', 'SUBSCRIPTION'), ('external','EXTERNAL'))
    course_over_view = models.ForeignKey(CourseOverview, related_name='course_over_view', on_delete=models.CASCADE)
    banner_img_url_txt = models.TextField(blank=True, default=u"")
    banner_img = models.ImageField(upload_to = 'banner/lms/courses')
    enabled = models.BooleanField(default = True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, )
    slide_position = models.IntegerField()
    link_type = models.CharField(max_length=20, choices=LINK_CHOICES, default='ABOUT')
    link_url =models.TextField(blank=True, default=u"")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add = True)
    updated_time = models.DateTimeField(auto_now=True)







