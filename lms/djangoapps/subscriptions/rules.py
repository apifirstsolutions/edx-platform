from django.db.models import Q
from bridgekeeper.rules import EMPTY, Rule
from enterprise.models import (
  EnterpriseCustomer,
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
    if bundle.enterprise_id is None: return True
    
    return EnterpriseCustomerUser.objects.filter(enterprise_customer_id=bundle.enterprise_id, user_id=user.id).exists()

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
  def check(self, user, plan=None):
    if not plan.is_active: return False
    if plan.enterprise is None: return True
    else:
      return EnterpriseCustomerUser.objects.filter(enterprise_customer_id=plan.enterprise.id, user_id=user.id).exists()

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
  def check(self, user, plan=None):
    if user.is_anonymous: return False

    enterprise_user_qs = EnterpriseCustomerUser.objects.filter(user_id=user.id)
   
    if not enterprise_user_qs.exists():
      have_subscription = Subscription.objects.filter(subscription_plan=plan, user=user).exists()
      return have_subscription
    else:
      enterprise_user = enterprise_user_qs.first()
      enterprise =  EnterpriseCustomer.objects.get(uuid=enterprise_user.enterprise_customer_id)
      return Subscription.objects.filter(subscription_plan=plan, enterprise=enterprise).exists()
    
  def query(self, user):
    return Q(pk__in=[])
    
class CanSubscribeToPlan(Rule): 
  """
    A rule that defines who can subscribe a plan
    - If not anonymous user
    - Plan is active
    - If User has not subscribed or subscription is cancelled
    - If the Subscription Plan is not tied to an Enterprise
  """
  def check(self, user, plan=None):
    if user.is_anonymous: return False
    if not plan.is_active: return False
    if plan.enterprise_id is not None: return False

    have_active_subscription = \
      Subscription.objects.filter(subscription_plan_id=plan.id, user_id=user.id, status='active').exists()

    return not have_active_subscription
    
  
  def query(self, user):
    return Q(pk__in=[])

class IsEnterpriseAdminForBundle(Rule): 
  """
    Return true if user is Enterprise Admin for an Enterprise Bundle 
  """
  def check(self, user, bundle=None):
    if bundle is None or bundle.enterprise_id is None:
      return False
    
    isEnterpriseUser = EnterpriseCustomerUser.objects.filter(enterprise_customer_id=bundle.enterprise_id, user_id=user.id).exists()
    
    if not isEnterpriseUser:
      return False
    
    return SystemWideEnterpriseUserRoleAssignment.objects.filter(role__name='enterprise_admin', user_id=user.id).exists()

  def query(self, user):
    return Q(pk__in=[])


class CanAccessCourse(Rule): 
  """
    Checks who can start a course 
  """
  def check(self, user, course=None):
    return True

  def query(self, user):
    return Q(pk__in=[])
  