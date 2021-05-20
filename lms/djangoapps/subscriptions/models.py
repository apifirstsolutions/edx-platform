import collections
from enum import Enum
from django.db import models
from jsonfield.fields import JSONField
from enterprise.models import EnterpriseCustomer
from django.contrib.auth.models import User
from .helpers.unique_slugify import unique_slugify
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

class Statuses(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'
class BillingCycles(Enum):
    MONTH = 'month'
    YEAR = 'year'
    ONE_TIME = 'one-time'

class SubscriptionTransaction(Enum):
    CREATE = 'CREATED'
    RENEWAL = 'RENEWAL'
    CANCEL = 'CANCELLED'
class Bundle(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    slug = models.SlugField(max_length=200, blank=True)
    courses = models.ManyToManyField(CourseOverview)
    description = models.CharField(max_length=500, default=None, null=True, blank=True)
    enterprise = models.ForeignKey(EnterpriseCustomer, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.slug

    def save(self, **kwargs):
        unique_slugify(self, self.name) 
        super(Bundle, self).save(**kwargs)
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    slug = models.SlugField(max_length=200, blank=True)
    
    bundle = models.ForeignKey(Bundle, on_delete=models.DO_NOTHING, null=True, blank=True)
    description = models.CharField(max_length=500, default=None, null=True, blank=True)
    ecommerce_prod_id = models.IntegerField(default=None, null=True, blank=True, verbose_name='Ecommerce Product ID')  # FIXME
    enterprise = models.ForeignKey(EnterpriseCustomer, on_delete=models.DO_NOTHING, null=True, blank=True)
    grace_period = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    price_month = models.DecimalField(max_digits=6, decimal_places=2, default=None, null=True, blank=True)
    price_onetime = models.DecimalField(max_digits=6, decimal_places=2, default=None, null=True, blank=True)
    price_year = models.DecimalField(max_digits=6, decimal_places=2, default=None, null=True, blank=True)
    stripe_prod_id = models.CharField(max_length=50, null=False, blank=False, verbose_name='Stripe Product ID')
    stripe_price_month_id = models.CharField(max_length=50, null=True, blank=True, verbose_name='Stripe Price ID (month)')
    stripe_price_year_id = models.CharField(max_length=50, null=True, blank=True, verbose_name='Stripe Product ID (year)')
    
    valid_until = models.DateTimeField(default=None, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.slug

    def save(self, **kwargs):
        unique_slugify(self, self.name) 
        super(SubscriptionPlan, self).save(**kwargs)

class Subscription(models.Model):
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    billing_cycle = models.CharField(
      max_length=10,
      choices=[(cycle, cycle.value) for cycle in BillingCycles],
      default=BillingCycles.MONTH
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    enterprise = models.ForeignKey(EnterpriseCustomer, on_delete=models.CASCADE, null=True, blank=True)
    start_at = models.DateTimeField(default=None, null=True, blank=True)
    end_at = models.DateTimeField(default=None, null=True, blank=True)
    status = models.CharField(
      max_length=10,
      choices=[(status, status.value) for status in Statuses],
      default=Statuses.ACTIVE
    )
    license_count = models.IntegerField(default=1, null=False, blank=False)
    biller_subscription_id = models.CharField(max_length=50, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=50, null=False, blank=False)
    stripe_price_id = models.CharField(max_length=50, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email + '::' + self.subscription_plan.name
class License(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
      max_length=10,
      choices=[(status, status.value) for status in Statuses],
      default=Statuses.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email + '::' + subscription.billing_cycle + subscription.subscription_plan.name

class Transactions(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    status = models.CharField(
      max_length=10,
      choices=[(status, status.value) for status in Statuses],
      default=Statuses.ACTIVE
    )
    description = models.CharField(
      max_length=10,
      choices=[(trans, trans.value) for trans in SubscriptionTransaction],
      default=None,
      null=True,
      blank=True,
    )
    license_count = models.IntegerField()
    biller_invoice_id = models.CharField(max_length=50, default=None, null=True, blank=True)
    ecommerce_trans_id = models.IntegerField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '#' + self.id + ' - (' + subscription.billing_cycle + ')' + subscription.subscription_plan.name
