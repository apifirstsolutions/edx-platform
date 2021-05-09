import collections
from django.db import models
from jsonfield.fields import JSONField

class Bundle(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    course_metadata = JSONField(
        null=False,
        blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )
    product_id = models.IntegerField()
    description = models.CharField(max_length=500, default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    bundle_id = models.IntegerField()
    product_id = models.IntegerField()
    description = models.CharField(max_length=500, default=None, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    valid_until = models.DateTimeField(default=None, null=True, blank=True)
    billing_cycle_options = models.CharField(max_length=50)
    grace_period = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Subscription(models.Model):
    customer_id = models.IntegerField()
    is_enterprise = models.BooleanField(default=False)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    billing_cycle = models.CharField(max_length=20)
    start_at = models.DateTimeField(default=None, null=True, blank=True)
    end_at = models.DateTimeField(default=None, null=True, blank=True)
    status = models.CharField(max_length=20)
    license_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Subscription: ' + self.subscription_plan.name