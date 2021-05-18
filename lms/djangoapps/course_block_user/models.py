from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class CourseBlockUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_id_block = models.CharField(max_length=255, null=True, blank=True, default=None)
    block_mobile_view = models.TextField(blank=True, null=True)
    descendants = models.TextField(blank=True, null=True)
    processed_descendants = models.IntegerField(blank=True, null=True)


