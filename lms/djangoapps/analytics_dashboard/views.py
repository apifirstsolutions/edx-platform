# -*- coding: utf-8 -*-
import json
from datetime import datetime, date, timedelta

from django.http import Http404
from django.urls import reverse
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required

from common.djangoapps.student.models import UserProfile, CourseEnrollmentManager
from common.djangoapps.student.models import CourseEnrollment, CourseAccessRole
from common.djangoapps.student.views.dashboard import (
    get_org_black_and_whitelist_for_site,
    get_course_enrollments,
    get_dashboard_course_limit,
    get_filtered_course_entitlements,
)

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview, Category, SubCategory
from lms.djangoapps.custom_form_app.custom_reg_form.models import UserExtraInfo

from lms.djangoapps.analytics_dashboard.filters import CourseFilter
from lms.djangoapps.analytics_dashboard.demographics import (
    calculate_age,
    spread_age_distribution,
    median,
    age_dist,
    get_learners_gender_list,
    get_learners_edu
)
from lms.djangoapps.analytics_dashboard.trainer_helper import (
    spread_course_by_month,
    spread_course_by_year,
    spread_revenue_by_month,
    spread_revenue_by_month_from_orders_api,
    get_course_enrollment,
    get_orders_details,
    str_to_datetime,
    orders_by_quarter,
)

from logging import getLogger
log = getLogger(__name__)


@ensure_csrf_cookie
@login_required
def learner_profile_view(request, *args, **kwargs):
    user = request.user
    if not UserProfile.objects.filter(user=user).exists():
        return redirect(reverse('account_settings'))

    disable_course_limit = request and 'course_limit' in request.GET
    course_limit = get_dashboard_course_limit() if not disable_course_limit else None

    # Get the org whitelist or the org blacklist for the current site
    site_org_whitelist, site_org_blacklist = get_org_black_and_whitelist_for_site()
    course_enrollments = list(
        get_course_enrollments(user, site_org_whitelist, site_org_blacklist, course_limit, request=request))

    # Get the entitlements for the user and a mapping to all available sessions for that entitlement
    # If an entitlement has no available sessions, pass through a mock course overview object
    (course_entitlements,
     course_entitlement_available_sessions,
     unfulfilled_entitlement_pseudo_sessions) = get_filtered_course_entitlements(
        user,
        site_org_whitelist,
        site_org_blacklist
    )

    # Sort the enrollment pairs by the enrollment date
    course_enrollments.sort(key=lambda x: x.created, reverse=True)

    # Filter out any course enrollment course cards that are associated with fulfilled entitlements
    for entitlement in [e for e in course_entitlements if e.enrollment_course_run is not None]:
        course_enrollments = [
            enr for enr in course_enrollments if entitlement.enrollment_course_run.course_id != enr.course_id
        ]

    web_course_enrollments = []
    for course in course_enrollments:
        platform = course._course_overview.platform_visibility
        if platform is None or platform == 'Web' or platform == 'Both':
            web_course_enrollments.append(course)

    in_progress_courses = []
    completed_courses = []
    for course in course_enrollments:
        if course.completed_units == course.total_units:
            completed_courses.append(course)
        else:
            in_progress_courses.append(course)

    user_id = request.user.id
    try:
        learner = User.objects.filter(id=user_id).get()
        log.info("Fetched User for logged in user id %s", str(user_id))
    except:
        raise Http404("Invalid user id %s", str(user_id))

    learner_profile = UserProfile.objects.filter(user=learner).get()
    log.info("Fetched UserProfile data for the user %s", str(learner.username))

    context = {
        'learner': learner,
        'profile': learner_profile,
        'course_enrollments': web_course_enrollments,
        'course_entitlements': course_entitlements,
        'in_progress_courses': in_progress_courses,
        'completed_courses': completed_courses,
    }

    return render(request, 'analytics_dashboard/learner_profile.html', context)


@ensure_csrf_cookie
@login_required
def admin_view(request, *args, **kwargs):
    course_learner_count = CourseEnrollment.objects.filter().values('course_id').annotate(
        total=Count('course_id')).order_by('-total')
    log.info("Fetched Learner count from CourseEnrollment")

    trainer_total_learner_count = sum([x['total'] for x in course_learner_count])

    total_learners = User.objects.filter(is_active=1, is_staff=0, is_superuser=0).count()
    log.info("Fetched User objects to list total learners")

    trainer_courses = CourseOverview.objects.filter()\
        .values(
        'id',
        'display_name',
        'start_date',
        'difficulty_level',
        'new_category__name',
        'subcategory__name',
        'course_price',
        'created'
    )
    log.info("Fetched Course Overview to list the Courses")

    trainer_courses_count = trainer_courses.count()

    courses_filter = CourseFilter(request.GET, queryset=trainer_courses)
    trainer_courses = courses_filter.qs

    paginator = Paginator(trainer_courses, 15)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    if page.has_next():
        next_url = f'?page={page.next_page_number()}'
    else:
        next_url = ''

    if page.has_previous():
        prev_url = f'?page={page.previous_page_number()}'
    else:
        prev_url = ''

    all_courses = CourseOverview.objects.filter().values()
    log.info("Fetched CourseOverview")
    trainer_course_month = spread_course_by_month(all_courses, 'created')

    category_list = Category.objects.values_list('id', 'name')
    log.info("Fetched Category for dropdown list")

    category_course_ids = {}
    for i, category in category_list:
        course = CourseOverview.objects.filter(new_category_id=i).values()
        category_course_ids[category] = [str(c['id']) for c in course]

    category_count = {}
    for k,v in category_course_ids.items():
        cnt = CourseEnrollment.objects.filter(course_id__in=v).count()
        category_count[k] = cnt
    log.info("Fetched CourseEnrollment to list the category count %s", str(category_count))

    context = {
        'trainer_courses': page,
        'trainer_courses_count': trainer_courses_count,
        'courses_filter': courses_filter,
        'trainer_total_learner_count': trainer_total_learner_count,
        'trainer_course_learner_count': course_learner_count,
        'trainer_course_year': trainer_course_month,
        'total_learners': total_learners,
        'category_count': category_count,
        'next_url': next_url,
        'prev_url': prev_url,
    }

    return render(request, 'analytics_dashboard/admin_dashboard.html', context)

@ensure_csrf_cookie
@login_required
def trainer_view(request, duration=1, *args, **kwargs):

    user = request.user
    user_id = user.id

    try:
        trainer = User.objects.filter(id=user_id, is_staff=1).get()
    except:
        raise Http404("Invalid user %s", str(user_id))

    trainer_profile = UserProfile.objects.filter(user=trainer).values()
    log.info("Fetched %s Trainer's user profile from UserProfile", str(trainer.username))

    trainer_course_ids = CourseAccessRole.objects \
        .filter(user_id=user_id, role='instructor') \
        .values_list('course_id')
    log.info("Fetched CourseAccessRole for user id %s", str(user_id))

    if duration is None or duration == '':
        trainer_course_learner_count = CourseEnrollment.objects \
            .filter(course_id__in=trainer_course_ids) \
            .values('course_id') \
            .annotate(total=Count('course_id')) \
            .order_by('-total')
    elif duration == 1:
        trainer_course_learner_count = CourseEnrollment.objects \
            .filter(course_id__in=trainer_course_ids, created__range=[date.today(), date.today() + timedelta(days=6)]) \
            .values('course_id') \
            .annotate(total=Count('course_id')) \
            .order_by('-total')
    elif duration == 2:
        trainer_course_learner_count = CourseEnrollment.objects \
            .filter(course_id__in=trainer_course_ids, created__month=datetime.today().month) \
            .values('course_id') \
            .annotate(total=Count('course_id')) \
            .order_by('-total')
    else:
        trainer_course_learner_count = CourseEnrollment.objects \
            .filter(course_id__in=trainer_course_ids,
                    created__month__lte=datetime.today().month,
                    created__month__gte=datetime.today().month - 2) \
            .values('course_id') \
            .annotate(total=Count('course_id')) \
            .order_by('-total')
    log.info("Fetched CourseEnrollment for trainer courses")

    trainer_total_learner_count = sum([x['total'] for x in trainer_course_learner_count])
    trainer_total_learner_label = [ c.get("course_id") for c in trainer_course_learner_count]

    chart_label = [str(i) for i in trainer_total_learner_label]

    trainer_courses = CourseOverview.objects.filter(id__in=trainer_course_ids).values()
    log.info("Fetched CourseOverview for trainer courses")

    if trainer_courses.count() > 0:
        trainer_course_month = spread_course_by_month(trainer_courses, 'created')
        trainer_course_year = spread_course_by_year(trainer_courses, 'created')
    else:
        trainer_course_month = {}

    context = {
        'user_id': user_id,
        'trainer': trainer,
        'duration': duration,
        'trainer_profile': trainer_profile,
        'trainer_courses': trainer_courses,
        'trainer_total_learner_count': trainer_total_learner_count,
        'trainer_course_learner_count': trainer_course_learner_count,
        'trainer_total_learner_label': trainer_total_learner_label,
        'chart_label': json.dumps(chart_label),
        'trainer_course_month': trainer_course_month,
        'trainer_course_year': trainer_course_month
    }

    return render(request, 'analytics_dashboard/trainer_dashboard.html', context)

@ensure_csrf_cookie
@login_required
def trainer_course_detail_view(request, course_id, *args, **kwargs):
    log.info("Course id: %s", str(course_id))
    user = request.user

    course = CourseOverview.objects.get(id=course_id)
    log.info("Fetched CourseOverview for course %s", str(course_id))

    course_learners = CourseEnrollment.objects.filter(course_id=course_id).exclude(user_id=user.id)
    log.info("Fetched CourseEnrollment for course %s", str(course_id))

    course_completions = 0
    learner_enrollments = []
    for i, l in enumerate(course_learners):
        course_enrollment = get_course_enrollment(request, l.user)
        for j, k in enumerate(course_enrollment):
            if str(k.course_id) == course_id:
                learner_enrollments.append(k)
                if k.completed_units == k.total_units:
                    course_completions += 1

    context = {
        'course_id': course_id,
        'course': course,
        'course_learners_count': len(list(course_learners)),
        'enrollments': learner_enrollments,
        'course_completions': course_completions,
    }

    return render(request, 'analytics_dashboard/trainer_course_detail.html', context)


@ensure_csrf_cookie
@login_required
def revenue_view(request, duration=1, *args, **kwargs):
    user = request.user
    if not user.is_superuser:
        raise Exception("Not authenticated")

    orders = get_orders_details(request)['result']

    orders_revenue_by_month = spread_revenue_by_month_from_orders_api(orders, 'order_date')

    orders_by_quarter(orders_revenue_by_month, quarter=duration)

    orders_sum  = sum(float(order['price']) for order in orders)

    current_month_revenue = sum(float(order['price']) for order in orders if str_to_datetime(order['order_date']).month == datetime.now().month)

    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    if page.has_next():
        next_url = f'?page={page.next_page_number()}'
    else:
        next_url = ''

    if page.has_previous():
        prev_url = f'?page={page.previous_page_number()}'
    else:
        prev_url = ''

    context = {
            'orders': page,
            'duration': duration,
            'orders_filter': orders,
            'orders_sum': orders_sum,
            'current_month_revenue': current_month_revenue,
            'orders_revenue_by_month': orders_revenue_by_month,
            'next_url': next_url,
            'prev_url': prev_url,
        }
    return render(request, 'analytics_dashboard/admin_revenue.html', context)


@ensure_csrf_cookie
@login_required
def demographics_view(request):
    learners_all = User.objects.filter(is_active=1, is_staff=0, is_superuser=0).values()

    learners_gender_list = get_learners_gender_list([l["id"] for l in learners_all])
    learners_edu = get_learners_edu([l["id"] for l in learners_all])

    learners_yob = UserExtraInfo.objects.filter(user__in=[l["id"] for l in learners_all]).values()
    log.info("Fetched UserExtraInfo for all learner users")

    learners_age = [calculate_age(l["date_of_birth"]) for l in learners_yob]
    learners_age_list = spread_age_distribution(learners_age)

    context = {
        'learners_all': learners_all,
        'learners_gender': learners_gender_list,
        'learners_edu': learners_edu,
        'learners_age_list': learners_age_list,
        'age_median': median(learners_age),
        'age_dist': age_dist(learners_age)
    }

    return render(request, 'analytics_dashboard/admin_demographics.html', context)
