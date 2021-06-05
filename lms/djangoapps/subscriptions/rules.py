from django.db.models import Q
from bridgekeeper.rules import Rule
from enterprise.models import (
    EnterpriseCustomerUser, 
    SystemWideEnterpriseRole, 
    SystemWideEnterpriseUserRoleAssignment,
)
from .models import Subscription

class CanViewBundle(Rule):
  """
    A rule that defines who can view a bundle

    Return True if the Bundle is not tied to any Enterprise.
    If it is tied to an Enterprise, only users of that Enterprise can view it.
  """
  def check(self, user, bundle=None):
    if bundle is None:
      return False
    
    if bundle.enterprise_id is None:
      return True
    
    return EnterpriseCustomerUser.objects.filter(enterprise_customer_id=bundle.enterprise_id, user_id=user.id, linked=1).exists()

  def query(self, user):
    # Return an always-empty queryset filter so that this always
    # fails permissions, but still passes the is_possible_for check
    # that is used to determine if the rule should allow a user
    # into django admin
    return Q(pk__in=[])


class ViewSubscriptionPlan(Rule):
  """
    A rule that defines who can view a plan

    Return True if the Plan is not tied to any Enterprise.
    If it is tied to an Enterprise, only users of that Enterprise can view it.
    Also checks if Plan is active
  """
  def check(self, user, plan=None):
    if plan is None or not plan.is_active:
      return False
    
    if plan.enterprise_id is None:
      return True
    
    return EnterpriseCustomerUser.objects.filter(enterprise_customer_id=plan.enterprise_id, user_id=user.id, linked=1).exists()

  def query(self, user):
    # Return an always-empty queryset filter so that this always
    # fails permissions, but still passes the is_possible_for check
    # that is used to determine if the rule should allow a user
    # into django admin
    return Q(pk__in=[])

class CanSubscribeToPlan(Rule): 
  """
    A rule that defines who can subscribe a plan

    Return True if the Plan is not tied to an Enterprise and user has no active subscription to it.
    Also checks if Plan is active
  """
  def check(self, user, plan=None):
    if plan is None or not plan.is_active:
      return False

    hasSubscription = Subscription.objects.filter(subscription_plan_id=plan.id, user_id=user.id).exists()
    return plan.enterprise_id is None and not hasSubscription

  def query(self, user):
    # Return an always-empty queryset filter so that this always
    # fails permissions, but still passes the is_possible_for check
    # that is used to determine if the rule should allow a user
    # into django admin
    return Q(pk__in=[])
  
class IsEnterpriseAdminForBundle(Rule): 
  """
    Return true if user is Enterprise Admin for an Enterprise Bundle 
  """
  def check(self, user, instance=None):
    if instance is None or instance.enterprise_id is None:
      return False
    
    isEnterpriseUser = EnterpriseCustomerUser.objects.filter(enterprise_customer_id=instance.enterprise_id, user_id=user.id, linked=1).exists()
    
    if not isEnterpriseUser:
      return False
    
    return SystemWideEnterpriseUserRoleAssignment.objects.filter(role__name='enterprise_admin', user_id=user.id, linked=1).exists()

  def query(self, user):
    # Return an always-empty queryset filter so that this always
    # fails permissions, but still passes the is_possible_for check
    # that is used to determine if the rule should allow a user
    # into django admin
    return Q(pk__in=[])