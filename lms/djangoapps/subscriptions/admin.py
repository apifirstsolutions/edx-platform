from django.contrib import admin

from .models import Bundle, Subscription, SubscriptionPlan

admin.site.register(Bundle)
admin.site.register(SubscriptionPlan)
admin.site.register(Subscription)