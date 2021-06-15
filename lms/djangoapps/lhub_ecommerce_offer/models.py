from django.db import models
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from django.utils.translation import gettext_lazy as _



class Offer(models.Model):
    PERCENTAGE, FIXED = ("Percentage", "Absolute")
    TYPE_CHOICES = (
        (PERCENTAGE, _("Discount is a percentage off of the product's value")),
        (FIXED, _("Discount is a fixed amount off of the product's value")),
    )
    incentive_type = models.CharField(
        _("Type"), max_length=250, choices=TYPE_CHOICES, blank=True)
    incentive_value = models.DecimalField(max_digits=12, decimal_places=2)
    condition_type = models.CharField(max_length=250)
    condition_value = models.DecimalField(max_digits=12, decimal_places=2)
    start_datetime = models.DateTimeField('start datetime')
    end_datetime = models.DateTimeField('end datetime', null=True ,blank=True)
    priority = models.IntegerField()
    is_exclusive = models.BooleanField()
    associated_ecommerce_offer_id = models.IntegerField()
    course = models.ManyToManyField(CourseOverview)
    is_suspended = models.BooleanField(default=False)
    
    class Meta(object):
        app_label = "lhub_ecommerce_offer"



class Coupon(models.Model):
    name = models.CharField(max_length=250)
    coupon_code = models.CharField(max_length=250)

    PERCENTAGE, FIXED = ("Percentage", "Absolute")
    TYPE_CHOICES = (
        (PERCENTAGE, _("Discount is a percentage off of the product's value")),
        (FIXED, _("Discount is a fixed amount off of the product's value")),
    )
    incentive_type = models.CharField(
        _("Type"), max_length=250, choices=TYPE_CHOICES, blank=True)

    incentive_value = models.DecimalField(max_digits=12, decimal_places=2)
    usage = models.CharField(max_length=250)
    start_datetime = models.DateTimeField('start date')
    end_datetime = models.DateTimeField('end date')
    is_exclusive = models.BooleanField()
    course = models.ManyToManyField(CourseOverview)
    associated_ecommerce_coupon_id = models.IntegerField()
    
    class Meta(object):
        app_label = "lhub_ecommerce_offer"
