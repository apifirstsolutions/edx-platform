
import logging

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from enterprise.models import EnterpriseCustomer, EnterpriseCustomerUser

from .models import Subscription, Statuses
from .services.subscription import SubscriptionService

logger = logging.getLogger(__name__)
subscription_svc = SubscriptionService() 

@receiver(user_logged_in, dispatch_uid='subscriptions.user_login')
def user_login(request, user, **kwargs):

    if not user.is_anonymous:

        entries = EnterpriseCustomerUser.objects.filter(user_id=user.id)
    
        if entries.exists():
            for enterprise_user in entries:
                try:
                    enterprise = EnterpriseCustomer.objects.get(uuid=enterprise_user.enterprise_customer_id)  
                    subscriptions = Subscription.objects.filter(enterprise=enterprise, status=Statuses.ACTIVE.value)

                    # if have active subscriptions, assign course entitlements and subscription license
                    for subscription in subscriptions:
                        subscription_svc.assign_licenses_n_entitlements(user, subscription)
                except EnterpriseCustomer.DoesNotExist:
                    pass

  
