from django.urls import path
from ..views import webhook

urlpatterns = [
    path('stripe/webhook', webhook.stripe_webhook_view),
]
