from django.http import Http404
from django.template import TemplateDoesNotExist
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from bridgekeeper import perms
from mako.exceptions import TopLevelLookupException
from django.utils.translation import ugettext_lazy as _

from common.djangoapps.util.cache import cache_if_anonymous
from common.djangoapps.edxmako.shortcuts import render_to_response
from lms.djangoapps.courseware.context_processor import user_timezone_locale_prefs


from enterprise.models import (
    EnterpriseCustomerUser,
)

from ..models import Subscription, SubscriptionPlan
from ..permissions import VIEW_SUBSCRIPTION_PLAN




@ensure_csrf_cookie
@cache_if_anonymous()
def plan_view(request, slug):
    
    plan = SubscriptionPlan.objects.get(slug=slug)
    
    if not perms[VIEW_SUBSCRIPTION_PLAN].check(request.user, plan):
        raise Http404()

    options = []
    
    if (plan.price_month is not None):
        options.append(('month', '/month', plan.price_month, plan.slug + '-month'))
    if (plan.price_year is not None):
        options.append(('year', '/year', plan.price_year, plan.slug + '-year'))
    if (plan.price_onetime is not None):
        options.append(('onetime', 'one-time pay', plan.price_onetime, plan.slug + '-onetime'))

    try:
        context = {
            "name": plan.name,
            "description": plan.description,
            "courses": plan.bundle.courses.all(),
            "options": options,
            "image_url": plan.image_url,
        }
        return render_to_response('subscriptions/plan_view.html', context, content_type='text/html')

    except TopLevelLookupException:
        raise Http404
    except TemplateDoesNotExist:
        raise Http404



@login_required
@ensure_csrf_cookie
def my_bundled_courses(request):

    user = request.user
    user_timezone_locale = user_timezone_locale_prefs(request)
    user_timezone = user_timezone_locale['user_timezone']

    all_subscriptions = Subscription.objects.filter(user=user)
    enterprise_user_qs = EnterpriseCustomerUser.objects.filter(user_id=user.id, linked=1)

    if enterprise_user_qs.exists():
        enterprise_user = enterprise_user_qs.first()
        all_enterprise_subscriptions = Subscription.objects.filter(enterprise__id=enterprise_user.enterprise_customer_id)
        all_subscriptions.extend(all_enterprise_subscriptions)

    try:
        context = {
            'name': 'My Bundled Courses',
            'subscriptions': all_subscriptions,
            'user_timezone': user_timezone,
        }

        return render_to_response('subscriptions/my_bundled_courses.html', context, content_type='text/html')

    except TopLevelLookupException:
        raise Http404
    except TemplateDoesNotExist:
        raise Http404        