from django.http import Http404
from django.template import TemplateDoesNotExist
from django.views.decorators.csrf import ensure_csrf_cookie
from bridgekeeper import perms
from mako.exceptions import TopLevelLookupException

from common.djangoapps.util.cache import cache_if_anonymous
from common.djangoapps.edxmako.shortcuts import render_to_response

from ..models import SubscriptionPlan
from ..permissions import VIEW_SUBSCRIPTION_PLAN


@ensure_csrf_cookie
@cache_if_anonymous()
def render_plan_view(request, template, slug):
    
    plan = SubscriptionPlan.objects.get(slug=slug)
    
    if not perms[VIEW_SUBSCRIPTION_PLAN].check(request.user, plan):
        raise Http404()

    options = []
    
    if (plan.price_month is not None):
        options.append(('month', '/month', plan.price_month, plan.stripe_price_month_id))
    if (plan.price_year is not None):
        options.append(('year', '/year', plan.price_year, plan.stripe_price_year_id))
    if (plan.price_onetime is not None):
        options.append(('one-time', 'one-time pay', plan.price_onetime, None))

    try:
        context = {
            "name": plan.name,
            "description": plan.description,
            "courses": plan.bundle.courses.all(),
            "options": options
        }
        return render_to_response('subscriptions/' + template, context, content_type='text/html')

    except TopLevelLookupException:
        raise Http404
    except TemplateDoesNotExist:
        raise Http404