import logging
from django.conf import settings
from slumber.exceptions import HttpClientError, HttpServerError
from edx_rest_api_client.client import EdxRestApiClient
from edx_rest_api_client.exceptions import SlumberBaseException
from openedx.core.djangoapps.commerce.utils import create_tracking_context, ecommerce_api_client

from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

log = logging.getLogger(__name__)

def _ecommerce_api_client(user, session=None):
    """ Custom ecommerce_api_client not using /api/v* in URL """
    
    claims = {'tracking_context': create_tracking_context(user)}
    scopes = [
        'user_id',
        'email',
        'profile'
    ]
    jwt = create_jwt_for_user(user, additional_claims=claims, scopes=scopes)

    return EdxRestApiClient(
        configuration_helpers.get_value('ECOMMERCE_INTERNAL_URL_ROOT', settings.ECOMMERCE_INTERNAL_URL_ROOT),
        jwt=jwt,
        session=session
    )

# Creates a Subscription Plan Product in Ecommerce
def create_ecommerce_product(user, product, prices):
    try:
        result = _ecommerce_api_client(user).subscription_hook.plan.post(product)

        if result['id'] is None:
            raise Exception()         

        return result
    except (HttpClientError, HttpServerError, SlumberBaseException, Exception):
        log.warning(u"Error occured while creating subscription product in ecommerce. ")
        raise


# Creates a StockRecords for prices in Ecommerce
def create_stockrecord(user, ecommerce_product_id, sku, price):
    try:
        stockrecord = {
            "product": ecommerce_product_id,
            "partner": 0,   # TODO DEFAULT PARTNER ID
            "partner_sku": sku,
            "price_currency": "SGD",
            "price_excl_tax": price
        }
        result = ecommerce_api_client(user).stockrecords.post(stockrecord)
        if result['id'] is None:
            raise Exception()         

        return result
    except (HttpClientError, HttpServerError, SlumberBaseException, Exception):
        log.warning(u"Error occured while creating subscription product in ecommerce. ")
        raise


# TODO
def update_ecommerce_product():
    pass   

def update_ecommerce_stockrecord():
    pass  

# Gets Stripe Customer ID from Ecommerce Records
def get_stripe_customer_id():
    pass

