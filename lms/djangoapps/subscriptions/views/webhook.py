
import json
import logging
import stripe

from lms.djangoapps.subscriptions.models import Subscription

from ..services.subscription import SubscriptionService 
from ..models import Subscription, Statuses



from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from lms.envs.common import STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET_KEY

log = logging.getLogger(__name__)

stripe.api_key = STRIPE_API_KEY

@csrf_exempt
def stripe_webhook_view(request):
  payload = request.body
  event = None
  sig_header = request.META['HTTP_STRIPE_SIGNATURE']

  try:
    event = stripe.Webhook.construct_event(
      payload, sig_header, STRIPE_WEBHOOK_SECRET_KEY
    )
  except ValueError as e:
    # Invalid payload
    return HttpResponse(status=400)
  except stripe.error.SignatureVerificationError as e:
    # Invalid signature
    return HttpResponse(status=400)

   # if stripe subscription status is cancelled, check if status in DB and cancel if not
  if event.type in [ 'customer.subscription.updated', 'customer.subscription.deleted' ]:
    subscription = event.data.object
    
    try:
      sub = Subscription.objects.get(stripe_subscription_id=subscription['id'])
      if sub.status not in [ Statuses.CANCELLED.value, Statuses.EXPIRED.value ]:
        SubscriptionService().cancel_subscription(sub)
      else:
        raise Exception("Subscription is already cancelled or expired.")

    except Subscription.DoesNotExist:
      log.error("Webhook Error: No subscription found in DB for Stripe subscription %s" % subscription['id'])
    except Exception as e:
      log.error("Webhook Error: handling stripe event %s for subscription " % (event.type, subscription['id']))

  else:
    log.error('Stripe Webhook unhandled event type %s' % (event.type))

  return HttpResponse(status=200)