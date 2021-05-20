import logging
from django import forms
from django.contrib import admin
from ..models import Subscription

logger = logging.getLogger(__name__)

admin.site.register(Subscription)