from django.db.models import Q
from bridgekeeper.rules import EMPTY, Rule
from datetime import datetime
import pytz 

from enterprise.models import (
  EnterpriseCustomer,
  EnterpriseCustomerUser, 
  SystemWideEnterpriseRole, 
  SystemWideEnterpriseUserRoleAssignment,
)
from .models import Subscription

utc=pytz.UTC
class CanViewBundle(Rule):
  """
    A rule that defines who can view a bundle

    - Bundle is not tied to any Enterprise.
    - If it is tied to an Enterprise, only users of that Enterprise can view it.
  """
  def check(self, user, bundle):
    if bundle.enterprise is not None:
      return EnterpriseCustomerUser.objects.filter(enterprise_customer=bundle.enterprise, user_id=user.id).exists()

    return True

  def query(self, user):
    # Return an always-empty queryset filter so that this always
    # fails permissions, but still passes the is_possible_for check
    # that is used to determine if the rule should allow a user
    # into django admin
    return Q(pk__in=[])
class CanViewSubscriptionPlan(Rule):
  """
    A rule that defines who can view a plan
    - If Plan is active
    - If the Plan is not tied to any Enterprise.
    - If it is tied to an Enterprise, only users of that Enterprise can view it.
  """
  def check(self, user, plan):
    valid_plan = (plan.valid_until > utc.localize(datetime.now())) & plan.is_active
    condition = valid_plan
    
    if plan.enterprise is not None:
      is_enterprise_member = EnterpriseCustomerUser.objects.filter(enterprise_customer=plan.enterprise, user_id=user.id).exists()
      condition &= is_enterprise_member

    return condition

  def query(self, user):
    is_enterprise_user = EnterpriseCustomerUser.objects.filter(user_id=user.id).exists()
    is_active = Q(is_active__exact=True)
    not_enterprise_plan = Q(enterprise__exact=None)
    query = is_active & not_enterprise_plan
    
    if is_enterprise_user:
      user_enterprise_customer_ids = EnterpriseCustomerUser.objects.filter(user_id=user.id).values('enterprise_customer_id')
      query = is_active & not_enterprise_plan | Q(enterprise__uuid__in=user_enterprise_customer_ids)
    
    return query

class CanViewSubscriptionPlanTracker(Rule): 
  """
    A rule that defines who can view a plan tracker page
    - If not anonymous user
    - If not Enterprise User, user has a subscription 
    - If Enterprise User, enterpise has a subscription 
  """
  def check(self, user, plan):
    
    condition = not user.is_anonymous

    if plan.enterprise is not None:
      is_enterprise_member = EnterpriseCustomerUser.objects.filter(
        enterprise_customer=plan.enterprise, user_id=user.id).exists()

      print("DEBUG  is_enterprise_member::", is_enterprise_member)

      enterprise_have_subscription = Subscription.objects.filter(
        subscription_plan=plan, enterprise=plan.enterprise).exists()

      print("DEBUG  enterprise_have_subscription::", enterprise_have_subscription)

      condition &= is_enterprise_member & enterprise_have_subscription
    else:
      user_has_subscription = Subscription.objects.filter(subscription_plan=plan, user=user).exists()
      condition &= user_has_subscription

    return condition
   
  def query(self, user):
    return Q(pk__in=[])
    
class CanSubscribeToPlan(Rule): 
  """
    A rule that defines who can subscribe a plan
    - If not anonymous user
    - Plan is active
    - If the Subscription Plan is not tied to an Enterprise
    - If User has not subscribed or subscription is cancelled
    
  """
  def check(self, user, plan):
    valid_plan = (plan.valid_until > utc.localize(datetime.now())) & plan.is_active
    condition = valid_plan
    
    if plan.enterprise is not None and user is not None:
      is_enterprise_member = EnterpriseCustomerUser.objects.filter(
        enterprise_customer=plan.enterprise, user_id=user.id).exists()
      
      enterprise_have_no_subscription = ~Subscription.objects.filter(
        subscription_plan=plan, enterprise=plan.enterprise).exists()
      
      condition &= is_enterprise_member & enterprise_have_no_subscription
    
    elif plan.enterprise is None and user is not None: 
      user_has_no_subscription = ~Subscription.objects.filter(
        subscription_plan=plan, user=user, status__in=['active', 'inactive']).exists()
      
      condition &= user_has_no_subscription

    return condition    
  
  def query(self, user):
    return Q(pk__in=[])

class IsEnterpriseAdminForBundle(Rule): 
  """
    Return true if user is Enterprise Admin for an Enterprise Bundle 
  """
  def check(self, user, bundle=None):
    if bundle is None or bundle.enterprise_id is None:
      return False
    
    isEnterpriseUser = EnterpriseCustomerUser.objects.filter(enterprise_customer=bundle.enterprise, user_id=user.id).exists()
    
    if not isEnterpriseUser:
      return False
    
    return SystemWideEnterpriseUserRoleAssignment.objects.filter(role__name='enterprise_admin', user=user).exists()

  def query(self, user):
    return Q(pk__in=[])
  