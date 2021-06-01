from django.contrib import admin
from .models import CourseTag, CourseTagType
# Register your models here.

admin.site.register(CourseTagType)
admin.site.register(CourseTag)
