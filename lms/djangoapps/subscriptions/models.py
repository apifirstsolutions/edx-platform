import collections
from django.db import models
from jsonfield.fields import JSONField
from enterprise.models import EnterpriseCustomer
from django.contrib.auth.models import User
class Bundle(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    course_metadata = JSONField(
        null=False,
        blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )
    description = models.CharField(max_length=500, default=None, null=True, blank=True)
    enterprise = models.ForeignKey(EnterpriseCustomer, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    bundle = models.ForeignKey(Bundle, on_delete=models.CASCADE, null=True, blank=False)
    product_id = models.IntegerField()
    description = models.CharField(max_length=500, default=None, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    valid_until = models.DateTimeField(default=None, null=True, blank=True)
    billing_cycle_options = JSONField(
        null=False,
        blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )
    grace_period = models.IntegerField()
    enterprise = models.ForeignKey(EnterpriseCustomer, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Subscription(models.Model):
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    billing_cycle = models.CharField(max_length=20)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    enterprise = models.ForeignKey(EnterpriseCustomer, on_delete=models.CASCADE, null=True, blank=True)
    start_at = models.DateTimeField(default=None, null=True, blank=True)
    end_at = models.DateTimeField(default=None, null=True, blank=True)
    status = models.CharField(max_length=20)
    license_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email + '::' + self.subscription_plan.name
class License(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email + '::' + subscription.billing_cycle + subscription.subscription_plan.name

