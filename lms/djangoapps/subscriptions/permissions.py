"""
Permission definitions for subscriptions djangoapp
"""

from bridgekeeper import perms, rules as bkRules
from .rules import CanViewBundle, ViewSubscriptionPlan, CanSubscribeToPlan, IsEnterpriseAdminForBundle

VIEW_BUNDLE = 'subscriptions.view_bundle'
EDIT_BUNDLE = 'subscriptions.edit_bundle'
VIEW_SUBSCRIPTION_PLAN = 'subscriptions.view_plan'
SUBSCRIBE_TO_PLAN = 'subscriptions.subscribe_to_plan'

perms[VIEW_BUNDLE] = CanViewBundle() | bkRules.is_staff
perms[EDIT_BUNDLE] = CanViewBundle() | IsEnterpriseAdminForBundle | bkRules.is_staff
perms[VIEW_SUBSCRIPTION_PLAN] = ViewSubscriptionPlan()
perms[SUBSCRIBE_TO_PLAN] = CanSubscribeToPlan()
