import json
import logging
import stripe

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from lms.envs.common import STRIPE_API_KEY

log = logging.getLogger(__name__)

stripe.api_key = STRIPE_API_KEY

@csrf_exempt
def stripe_webhook_view(request):
  payload = request.body
  event = None

  try:
    event = stripe.Event.construct_from(
      json.loads(payload), stripe.api_key
    )
  except ValueError as e:
    # Invalid payload
    return HttpResponse(status=400)

  # Handle the stripe events
  if event.type == 'customer.subscription.updated':
    subscription = event.data.object
    print("DEBUG customer.subscription.updated:::", subscription)

  elif event.type == 'customer.subscription.deleted':
    subscription = event.data.object 
    print("DEBUG customer.subscription.deleted:::", subscription)

  else:
    print('Stripe Webhook unhandled event type {}'.format(event.type))

  return HttpResponse(status=200)