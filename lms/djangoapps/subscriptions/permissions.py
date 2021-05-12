"""
Permission definitions for subscriptionns djangoapp
"""

from bridgekeeper import perms, is_staff
from .rules import CanViewBundle, CanSubscribeToBundle, IsEnterpriseAdminForBundle, has_role

VIEW_BUNDLE = 'subscriptions.view_bundle'
SUBSCRIBE_TO_BUNDLE = 'subscriptions.subscribe_to_bundle'
EDIT_BUNDLE = 'subscriptions.edit_bundle'

perms[VIEW_BUNDLE] = CanViewBundle() | is_staff
perms[SUBSCRIBE_TO_BUNDLE] = CanSubscribeToBundle()
perms[EDIT_BUNDLE] = CanViewBundle() | IsEnterpriseAdminForBundle | is_staff