import logging
from django import forms
from django.contrib import admin
from ..models import Bundle


logger = logging.getLogger(__name__)

class BundleForm(forms.ModelForm):
  class Meta:
    model = Bundle
    fields = ['name', 'slug', 'courses', 'enterprise',]

class BundleAdmin(admin.ModelAdmin):
  form = BundleForm
  fields = ['name', 'slug', 'courses', 'enterprise',]
  filter_horizontal = ['courses']
  readonly_fields = ['slug']
  search_fields = ['name', 'enterprise']
  list_display = ['slug', 'name', 'course_count', 'enterprise']

admin.site.register(Bundle, BundleAdmin)