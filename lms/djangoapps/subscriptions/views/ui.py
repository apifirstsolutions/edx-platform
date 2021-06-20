import logging
from itertools import chain
from bridgekeeper import perms
from mako.exceptions import TopLevelLookupException
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.template import TemplateDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

from openedx.core.djangoapps.catalog.utils import get_course_uuid_for_course
from enterprise.models import EnterpriseCustomerUser
from common.djangoapps.student.models import CourseEnrollmentState
from common.djangoapps.util.cache import cache_if_anonymous
from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.entitlements.models import CourseEntitlement
from lms.djangoapps.courseware.context_processor import user_timezone_locale_prefs

from ..models import Subscription, SubscriptionPlan
from ..permissions import (
    VIEW_SUBSCRIPTION_PLAN, 
    VIEW_SUBSCRIPTION_PLAN_TRACKER, 
    SUBSCRIBE_TO_PLAN,
)

logger = logging.getLogger(__name__)


@ensure_csrf_cookie
@cache_if_anonymous()
def plan_view(request, slug):
    
    user = request.user
    
    try:
        plan = SubscriptionPlan.objects.get(slug=slug)
    
        if not perms[VIEW_SUBSCRIPTION_PLAN].check(user, plan):
            logger.error("No VIEW_SUBSCRIPTION_PLAN permission.")
            raise Http404()

        options = []
        
        if (plan.price_month is not None):
            options.append(('month', '/month', plan.price_month, plan.slug + '-month'))
        if (plan.price_year is not None):
            options.append(('year', '/year', plan.price_year, plan.slug + '-year'))
        if (plan.price_onetime is not None):
            options.append(('onetime', 'one-time pay', plan.price_onetime, plan.slug + '-onetime'))

        context = {
            'name': plan.name,
            'description': plan.description,
            'courses': plan.bundle.courses.all(),
            'options': options,
            'image_url': plan.image_url,
            'can_subscribe': perms[SUBSCRIBE_TO_PLAN].check(user, plan)
        }
        return render_to_response('subscriptions/plan_view.html', context, content_type='text/html')

    except (SubscriptionPlan.DoesNotExist, TopLevelLookupException, TemplateDoesNotExist, Exception):
        
        raise Http404


@csrf_exempt
@cache_if_anonymous()
def plan_image(request, slug):
    try:
        plan = SubscriptionPlan.objects.get(slug=slug)
        return JsonResponse({ 'image_url': plan.image_url })
    except:
        return Response(
          { 'message': "Cannot retrieve image url for slug %s" % slug }, 
          status=HTTP_400_BAD_REQUEST
        )

@cache_if_anonymous()
def plan_list(request):
    
    try:
        context = {
            'courses': [],
            'course_discovery_meanings': None,
            'programs_list': [],
            'categories': [],
            'selected_category_name': None,
            'difficulty_levels': [],
            'selected_difficulty_level_id': None,
            'selected_mode': None,
            'sort': None,
            'banner_list': [],
            'show_categorized_view': None,
            'user_industry': None,
            'course_tag': None,
            'search_top':None
        }

        return render_to_response('subscriptions/plan_list.html', context, content_type='text/html')

    except SubscriptionPlan.DoesNotExist as e:
        logger.error(str(e))
        raise Http404
    except TopLevelLookupException as e:
        logger.error(str(e))
        raise Http404
    except TemplateDoesNotExist as e:
        logger.error(str(e))
        raise Http404
    except Exception as e:
        logger.error(str(e))
        raise Http404



@login_required
@ensure_csrf_cookie
def my_bundled_courses(request):

    user = request.user
    user_timezone_locale = user_timezone_locale_prefs(request)
    user_timezone = user_timezone_locale['user_timezone']

    subscriptions = Subscription.objects.filter(user=user)
   
    enterprise_user_qs = EnterpriseCustomerUser.objects.filter(user_id=user.id, linked=1)

    if enterprise_user_qs.exists():
        enterprise_user = enterprise_user_qs.first()
        enterprise_subscriptions = Subscription.objects.filter(enterprise__uuid=enterprise_user.enterprise_customer_id)
       

    
    all_subscriptions = list(chain(subscriptions, enterprise_subscriptions))

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

@login_required
@ensure_csrf_cookie
def my_bundled_courses_detail(request, slug):
    
    user = request.user
    
    try:
        plan = SubscriptionPlan.objects.get(slug=slug)
    
        if not perms[VIEW_SUBSCRIPTION_PLAN_TRACKER].check(user, plan):
            logger.error("No VIEW_SUBSCRIPTION_PLAN_TRACKER permission")
            raise Http404()

        options = []
        
        if (plan.price_month is not None):
            options.append(('month', '/month', plan.price_month, plan.slug + '-month'))
        if (plan.price_year is not None):
            options.append(('year', '/year', plan.price_year, plan.slug + '-year'))
        if (plan.price_onetime is not None):
            options.append(('onetime', 'one-time pay', plan.price_onetime, plan.slug + '-onetime'))

        context = {
            'name': plan.name,
            'description': plan.description,
            'courses': plan.bundle.courses.all(),
            'options': options,
            'image_url': plan.image_url,
            'can_subscribe': perms[SUBSCRIBE_TO_PLAN].check(user, plan)
        }
        return render_to_response('subscriptions/plan_view_tracker.html', context, content_type='text/html')

    except SubscriptionPlan.DoesNotExist as e:
        logger.error(str(e))
        raise Http404
    except TopLevelLookupException as e:
        logger.error(str(e))
        raise Http404
    except TemplateDoesNotExist as e:
        logger.error(str(e))
        raise Http404
    except Exception as e:
        logger.error(str(e))
        raise Http404

def bundled_courses_progress_list(request, slug):
    user = request.user
    plan = SubscriptionPlan.objects.filter(slug=slug)
    courses = plan.bundle.courses.all()

    enrollments_entitlements = []

    # for each course get enrollments or entitlements
    for course in courses: 
        enrollment = None
        entitlement = None   
        
        try:
            enrollment = CourseEnrollment.objects.get(course_id=course.id)
            enrollments_entitlements.append(enrollment)
        except CourseEnrollment.DoesNotExist:
            pass

        try: 
            course_uuid = get_course_uuid_for_course(str(course.id))
            entitlement = CourseEntitlement.objects.get(course_uuid=course_uuid)
            enrollments_entitlements.append(entitlement)
        except (CourseEntitlement.DoesNotExist, Exception) as e:
            logger.error("No enrollment or entitlement for a bundled course %s for user %s" % (course.id, user.username))
            pass

    return enrollments_entitlements