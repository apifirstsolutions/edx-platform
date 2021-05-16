"""
Permission definitions for subscriptions djangoapp
"""

from bridgekeeper import perms, rules as bkRules
from .rules import CanViewBundle, CanSubscribeToBundle, IsEnterpriseAdminForBundle

VIEW_BUNDLE = 'subscriptions.view_bundle'
SUBSCRIBE_TO_BUNDLE = 'subscriptions.subscribe_to_bundle'
EDIT_BUNDLE = 'subscriptions.edit_bundle'

perms[VIEW_BUNDLE] = CanViewBundle() | bkRules.is_staff
perms[SUBSCRIBE_TO_BUNDLE] = CanSubscribeToBundle()
perms[EDIT_BUNDLE] = CanViewBundle() | IsEnterpriseAdminForBundle | bkRules.is_staff