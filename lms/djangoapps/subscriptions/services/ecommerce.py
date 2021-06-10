import json
import logging
from django.conf import settings
from slumber.exceptions import HttpClientError, HttpServerError

from edx_rest_api_client.client import EdxRestApiClient
from edx_rest_api_client.exceptions import SlumberBaseException
from openedx.core.djangoapps.commerce.utils import create_tracking_context, ecommerce_api_client
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from lms.envs.common import SUBSCRIPTIONS_PARTNER_ID

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
def create_ecommerce_product(user, product, parent_id=None, cycle=None):
    try:
        if cycle is not None:
            # product_name = "%s (%s)", (product.name, cycle)
            product_name = product.name + ' ('+cycle+')'
        else:
            product_name = product.name
        
        product_data = {
            'title': product_name,
            'description': product.description,
            'is_public': True,
            'expires': product.valid_until,
        }

        if parent_id is not None:
            product_data['parent_id'] = parent_id

        serialized = json.dumps(product_data, indent=4, sort_keys=True, default=str)

        result = _ecommerce_api_client(user).subscription_hook.plan.post(serialized)

        if result['id'] is None:
            raise Exception()         

        return result
    
    except (HttpClientError, HttpServerError, SlumberBaseException, Exception):
        log.warning(u"Error occured while creating subscription product in ecommerce. ")
        raise


# Creates a StockRecords for prices in Ecommerce
def create_stockrecord(user, ecommerce_product_id, sku, price):
    stockrecord = { 'id': None }
    
    try:
        stockrecord = {
            "product_id": ecommerce_product_id,
            "partner_id": SUBSCRIPTIONS_PARTNER_ID,
            "partner_sku": sku,
            "price_currency": "SGD",
            "price_excl_tax": price
        }

        serialized = json.dumps(stockrecord, indent=4, sort_keys=True, default=str)

        result = _ecommerce_api_client(user).subscription_hook.stockrecords.post(serialized)
        
        if result['id'] is None:
            raise Exception()  

        stockrecord['id'] = result['id']

        return result
    
    except (HttpClientError, HttpServerError, SlumberBaseException, Exception):
        log.warning(u"Error occured while creating subscription product in ecommerce. ")
        raise


def update_ecommerce_product(user, product_id, name, description, valid_until):
    
    product_data = {}
    if name is not None:
        product_data['title'] = name
    if description is not None:
        product_data['description'] = description
    if valid_until is not None:
        product_data['valid_until'] = valid_until

    serialized = json.dumps(product_data, indent=4, sort_keys=True, default=str)
    
    try:
        _ecommerce_api_client(user).subscription_hook.plan(product_id).patch(serialized)
        # TODO if product have variants, change their name as well if not None
    except Exception as e:
        raise

def update_stockrecord_price(user, stockrecord_id, price):
    stockrecord_data = {
        'price_excl_tax': price
    }
    serialized = json.dumps(stockrecord_data, indent=4, sort_keys=True, default=str)

    try:
        _ecommerce_api_client(user).subscription_hook.stockrecords(stockrecord_id).patch(serialized)
    except Exception  as e:
        raise

# Gets Stripe Customer ID from Ecommerce Records
def get_stripe_customer_id():
    pass

