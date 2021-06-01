from django.contrib import admin
from .models import Offer, Coupon
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
import logging


# Register your models here.

class OfferAdmin(admin.ModelAdmin):
    """ Admin class for Offer model """
    fields = (
        'incentive_type',
        'incentive_value',
        'condition_type',
        'condition_value',
        'start_datetime',
        'end_datetime',
        'priority',
        'is_exclusive',
        'associated_ecommerce_offer_id',
        'course',
        'is_suspended'
    )
    list_display = [
        'incentive_type',
        'incentive_value',
        'condition_type',
        'condition_value',
        'start_datetime',
        'end_datetime',
        'priority',
        'is_exclusive',
        'associated_ecommerce_offer_id',
        'courses_sku',
        'is_suspended'
    ]


    def courses_sku(self, obj):
        pass



class CouponAdmin(admin.ModelAdmin):
    """ Coupon class for Offer model """
    fields = (
        'name',
        'coupon_code',
        'incentive_type',
        'incentive_value',
        'usage',
        'start_datetime',
        'end_datetime',
        'is_exclusive',
        'course',
        'associated_ecommerce_coupon_id',
    )
    list_display = [
        'name',
        'coupon_code',
        'incentive_type',
        'incentive_value',
        'usage',
        'start_datetime',
        'end_datetime',
        'is_exclusive',
        'courses_sku',
        'associated_ecommerce_coupon_id',
    ]


    def courses_sku(self, obj):
        pass


admin.site.register(Offer, OfferAdmin)
admin.site.register(Coupon, CouponAdmin)
