import logging
from django import forms
from django.contrib import admin
from ..models import Bundle

logger = logging.getLogger(__name__)

class BundleForm(forms.ModelForm):
  description = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))
  class Meta:
    model = Bundle
    fields = ['name', 'slug', 'description', 'courses', 'enterprise',]

class BundleAdmin(admin.ModelAdmin):
  form = BundleForm
  fields = ['name', 'slug', 'description', 'courses', 'enterprise',]
  filter_horizontal = ['courses']
  readonly_fields = ['slug']
  search_fields = ['name', 'description', 'enterprise__name']
  list_display = ['slug', 'name', 'enterprise']

admin.site.register(Bundle, BundleAdmin)