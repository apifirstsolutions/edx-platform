# -*- coding: utf-8 -*-
import random

import MySQLdb.cursors
from django.core.paginator import Paginator
from django.db import connection
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth, TruncYear
from datetime import datetime
from itertools import chain
import json


from lms.djangoapps.analytics_dashboard.demographics import (
    calculate_age,
    spread_age_distribution,
    median,
    age_dist,
    get_learners_gender_list,
    get_learners_edu
)
from lms.djangoapps.analytics_dashboard.filters import CourseFilter
# from lms.djangoapps.analytics_dashboard.filters import CourseFilter, OrderFilter
from lms.djangoapps.analytics_dashboard.trainer_helper import spread_course_by_month, spread_course_by_year, spread_revenue_by_month

from django.contrib.auth.models import User
from common.djangoapps.student.models import UserProfile, CourseEnrollmentManager
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.models import CourseEnrollment, CourseAccessRole
from custom_reg_form.models import UserExtraInfo

# from ecommerce.models import (
#     OrderOrder
# )

from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required

from common.djangoapps.student.views.dashboard import (
    get_org_black_and_whitelist_for_site,
    get_course_enrollments,
    get_dashboard_course_limit,
    get_filtered_course_entitlements,
)


def querySet_to_list(qs):
    """
    this will return python list<dict>
    """
    return [dict(q) for q in qs]



# Create your views here.
def index(request):
    course_count = CourseOverview.objects.count()
    print(f"Course count: {course_count}")

    enrollment = CourseEnrollment.objects.filter(
        user__username='learner1'
    ).order_by('created')

    context = {
        'course_count': course_count,
        'enrollment': enrollment
    }

    return render(request, 'analytics_dashboard/index.html', context)

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
    learner = User.objects.filter(id=user_id).get()

    learner_profile = UserProfile.objects.filter(user=learner).get()

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
    print(f'\nTrainers student: {course_learner_count}')

    trainer_total_learner_count = sum([x['total'] for x in course_learner_count])
    print(f'\nTotal learners: {trainer_total_learner_count}')

    total_learners = User.objects.filter(is_active=1, is_staff=0, is_superuser=0).count()
    print(f'Total Learners: {total_learners}')

    all_courses = CourseOverview.objects.filter().values()

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
    trainer_courses_count = trainer_courses.count()
    print(f'\nTrainer course count: {trainer_courses.count()}')

    courses_filter = CourseFilter(request.GET, queryset=trainer_courses)
    trainer_courses = courses_filter.qs
    # for c in trainer_courses:
    #     print('c', c['subcategory__name'])


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

    # print(f'Category')
    # for c in trainer_courses:
    #     print(c)
    #     if c:
    #         print(f'{c.new_category__name}')

    trainer_course_month = spread_course_by_month(all_courses, 'created')

    context = {
        'trainer_courses': page,
        'trainer_courses_count': trainer_courses_count,
        'courses_filter': courses_filter,
        'trainer_total_learner_count': trainer_total_learner_count,
        'trainer_course_learner_count': course_learner_count,
        'trainer_course_year': trainer_course_month,
        'total_learners': total_learners
    }

    return render(request, 'analytics_dashboard/admin_dashboard.html', context)

@ensure_csrf_cookie
@login_required
def trainer_view(request, *args, **kwargs):

    user = request.user
    user_id = user.id

    trainer = User.objects.filter(id=user_id, is_staff=1).get()
    trainer_profile = UserProfile.objects.filter(user=trainer).values()
    trainer_course_ids = CourseAccessRole.objects.filter(user_id=user_id, role='instructor').values_list(
        'course_id')

    trainer_course_learner_count = CourseEnrollment.objects.filter(course_id__in=trainer_course_ids).values(
        'course_id').annotate(total=Count('course_id')).order_by('-total')

    trainer_total_learner_count = sum([x['total'] for x in trainer_course_learner_count])
    trainer_total_learner_label = [ c.get("course_id") for c in trainer_course_learner_count]

    print('trainer label',trainer_total_learner_label)
    chart_label = []
    for i in trainer_total_learner_label:
        print("i", type(i), str(i))
        chart_label.append(str(i))
    print('chart_label', chart_label)

    trainer_courses = CourseOverview.objects.filter(id__in=trainer_course_ids).values()
    print(f'\nTrainer course count: {trainer_courses[0]}')

    if trainer_courses.count() > 0:
        trainer_course_month = spread_course_by_month(trainer_courses, 'created')
        trainer_course_year = spread_course_by_year(trainer_courses, 'created')
        print('trainer_course_month', trainer_course_month)
    else:
        trainer_course_month = {}

    context = {
        'user_id': user_id,
        'trainer': trainer,
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
def course_detail_view(request, course_id, *args, **kwargs):
    print(f'\nCourse id: {course_id}')
    course = CourseOverview.objects.get(id=course_id)

    course_learners = CourseEnrollment.objects.filter(course_id=course_id)

    def get_course_enrollment(request, user):
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

        return course_entitlements + web_course_enrollments

    course_completions = 0
    learner_enrollments = []
    for i, l in enumerate(course_learners):
        course_enrlmt = get_course_enrollment(request, l.user)
        for j, k in enumerate(course_enrlmt):
            if str(k.course_id) == course_id:
                print('enrollment', type(str(k.course_id)), k.course_id, type(course_id), course_id)
                learner_enrollments.append(k)
                print('learner_enrollments type', type(learner_enrollments))
                if k.completed_units == k.total_units:
                    course_completions += 1

    print('learner_enrollments', learner_enrollments)
    print('course_completions', course_completions)

    # ler = User.objects.prefetch_related('custom_reg_form_userextrainfo').all()
    # learners_info = UserExtraInfo.objects.filter(user_id__in=[l['user_id'] for l in course_learners]).extra(select={'created':'SELECT created FROM "edxapp"."student_courseenrollment" WHERE "edxapp"."student_courseenrollment".user_id = "edxapp"."CustomRegFormUserextrainfo".user_id'})


    # raw_sql = """select * from (select au.id as userid, crf.nric, crf.date_of_birth, au.username, au.first_name, au.last_name, au.email
    #             from edxapp.custom_reg_form_userextrainfo crf right join edxapp.auth_user au on crf.user_id = au.id) as q
    #             right join edxapp.student_courseenrollment sce on q.userid = sce.user_id where course_id = %s"""
    # learners_info = UserExtraInfo.objects.raw(raw_sql, [course_id])
    # print(f'\nInner join: \n{learners_info}')
    # print(f'\nLearner Info Type: \n{type(list(learners_info))}')
    #
    # print(f'\nLearners type {type(learners_info)}:')
    # # print(f'\nLearners ({learners_info.count()}):')
    # # for l in learners_info:
    # #     print(l.user.username)
    # learner_info_users = [l.user_id for l in learners_info]
    # print(f'\nLearners info users: {learner_info_users}:')
    #
    # learners_profile = UserProfile.objects.filter(user_id__in=learner_info_users).values().prefetch_related(
    #     'User')
    #
    # learners_all = User.objects.filter(id__in=learner_info_users, is_active=1).values()
    #
    # learners_gender_list = get_learners_gender_list([l["id"] for l in learners_all])
    # learners_edu = get_learners_edu([l["id"] for l in learners_all])
    #
    # learners_yob = UserExtraInfo.objects.filter(user__in=[l["id"] for l in learners_all]).values()
    #
    # learners_age = [calculate_age(l["date_of_birth"]) for l in learners_yob]
    # learners_age_list = spread_age_distribution(learners_age)

    context = {
        'course_id': course_id,
        'course': course,
        'course_learners_count': len(list(course_learners)),
        # 'course_learners': learners_info,
        # 'learners_profile': learners_profile,
        # 'learners_gender': learners_gender_list,
        # 'learners_edu': learners_edu,
        # 'learners_age_list': learners_age_list,
        # 'age_median': median(learners_age),
        # 'age_dist': age_dist(learners_age),
        'enrollments': learner_enrollments,
        'course_completions': course_completions,
    }

    return render(request, 'analytics_dashboard/trainer_course_detail.html', context)


@ensure_csrf_cookie
@login_required
def demographics_view(request):
    # trainer = User.objects.filter(id=user_id, is_staff=1).get()

    # trainer_course_ids = CourseAccessRole.objects.filter(user_id=user_id, role='instructor').values_list('course_id')
    #
    # print(f'\nTrainers students: \n{trainer_students.count()}')

    # course_enrolled_ids = [c['course_id'] for c in trainer_students]
    # courses = CourseOverview.objects.filter(id__in=course_enrolled_ids).values('id', 'display_name')
    # print(f'\nCourses: \n{courses}')

    # learners_by_trainer = User.objects.filter(id__in=[t['user_id'] for t in trainer_students]).values()
    # print(f'\nStudents by trainer: ')
    # for l in learners_by_trainer:
    #     print(f'{l["username"]}')

    # trainer_students_by_course_count = CourseEnrollment.objects.filter(course_id__in=trainer_course_ids).values('course_id').annotate(total=Count('course_id')).order_by('-total')
    # # for x in trainer_students_by_course_count
    # # print(f'\nTrainers students by course: \n{x.}')
    # print(f'\nTrainers students by course: \n{trainer_students_by_course_count}')

    learners_all = User.objects.filter(is_active=1, is_staff=0, is_superuser=0).values()
    print(f'\nTOTAL LEARNERS: {learners_all.count()}')

    learners_gender_list = get_learners_gender_list([l["id"] for l in learners_all])
    learners_edu = get_learners_edu([l["id"] for l in learners_all])
    print(f'\nUser id count: {len([l["id"] for l in learners_all])}')

    learners_yob = UserExtraInfo.objects.filter(user__in=[l["id"] for l in learners_all]).values()

    learners_age = [calculate_age(l["date_of_birth"]) for l in learners_yob]
    print(f'\nLearners age list count: {len(learners_age)}')
    learners_age_list = spread_age_distribution(learners_age)

    print(f'Age list: {learners_age}')
    print(f'Median age: {median(learners_age)}')
    print(f'\nAge dist: {age_dist(learners_age)}')

    context = {
        'learners_all': learners_all,
        'learners_gender': learners_gender_list,
        'learners_edu': learners_edu,
        'learners_age_list': learners_age_list,
        'age_median': median(learners_age),
        'age_dist': age_dist(learners_age)
    }

    return render(request, 'analytics_dashboard/admin_demographics.html', context)
#
#
# def demographics_by_course(request, user_id, course_id, *args, **kwargs):
#     print('demo by course')
#     print(f'\n user_id: {user_id}, course_id: {course_id}')
#
#     trainer = User.objects.filter(id=user_id, is_staff=1).get()
#
#     trainer_students = CourseEnrollment.objects.filter(course_id=course_id).values()
#     print(f'\nTrainers students ({len(trainer_students)}):')
#     for s in trainer_students:
#         print(f'{s["user_id"]}')
#
#     learners = UserProfile.objects.filter(id__in=[l['user_id'] for l in trainer_students]).values()
#     print(f'\nLearners: {learners}')
#
#     learners_gender = UserProfile.objects.filter(user__in=[l["id"] for l in learners]).values('gender').annotate(
#         total=Count('gender')).order_by('-total')
#     print(f'\n{learners_gender}')
#     for l in learners_gender:
#         if l['gender'] == 'm':
#             l['gender'] = 'Male'
#         if l['gender'] == 'f':
#             l['gender'] = 'Female'
#         if l['gender'] is None:
#             l['gender'] = 'Others'
#             print(f'{l["gender"]} {l["total"]}')
#         if l['gender'] == '':
#             l['gender'] = 'Not set by user'
#             print(f'{l["gender"]} {l["total"]}')
#
#     print([l["id"] for l in learners])
#     learners_edu = UserProfile.objects.filter(user__in=[l["id"] for l in learners]).values(
#         'level_of_education').annotate(total=Count('id')).order_by('-total')
#     print(f'\n{learners_edu.query}')
#
#     for l in learners_edu:
#         if l['level_of_education'] == 'p':
#             l['level_of_education'] = 'Doctorate'
#         if l['level_of_education'] == 'm':
#             l['level_of_education'] = 'Master’s or professional degree'
#         if l['level_of_education'] == 'b':
#             l['level_of_education'] = 'Bachelor’s degree'
#         if l['level_of_education'] == 'a':
#             l['level_of_education'] = 'Associate degree'
#         if l['level_of_education'] == 'hs':
#             l['level_of_education'] = 'Secondary/high school'
#         if l['level_of_education'] == 'jhs':
#             l['level_of_education'] = 'Junior secondary/junior high/middle school'
#         if l['level_of_education'] == 'el':
#             l['level_of_education'] = 'Elementary/primary school'
#         if l['level_of_education'] is None:
#             l['level_of_education'] = 'No Formal Education'
#         if l['level_of_education'] == '':
#             l['level_of_education'] = 'Not set by user'
#
#     context = {
#         'trainer': trainer,
#         'learners': learners,
#         'learners_gender': learners_gender,
#         'learners_edu': learners_edu,
#     }
#     return render(request, 'trainer_dashboard_demographics.html', context)
#
#
# def revenue_view(request, *args, **kwargs):
#     orders = OrderOrder.objects.select_related('user', ).filter().values().using('ecommerce')
#
#     orders_revenue_by_month = spread_revenue_by_month(orders, 'date_placed')
#     print(f'\nYearwise revenue: {orders_revenue_by_month}')
#
#     orders_filter = OrderFilter(request.GET, queryset=orders)
#     orders = orders_filter.qs
#
#     orders_sum = OrderOrder.objects.using('ecommerce') \
#         .aggregate(Sum('total_incl_tax'))['total_incl_tax__sum']
#
#     raw_sql = "SELECT monthname(o.date_placed) AS MONTH, sum(total_incl_tax) FROM ecommerce.order_order o where " \
#               "monthname(CURDATE()) = monthname(o.date_placed) group by monthname(o.date_placed) "
#
#     r1 = "SELECT * from ecommerce.order_order"
#
#     with connection.cursor() as cursor:
#         cursor.execute(raw_sql)
#         revenue_by_month = things = [{'month': row[0], 'revenue': row[1]} for row in cursor.fetchall()]
#
#     current_month_revenue = 1461.80
#     print(f'\nOrders by_month: {current_month_revenue}')
#     print(f'\nrevenue_by_month: {revenue_by_month}')
#     print(f'\nOrders sum: {orders_sum}')
#     print(f'\nOrders count: {orders.count()}')
#     # for o in orders:
#     #     print(f'{o.user.username} - \t{o.user.first_name} {o.user.last_name}')
#
#     paginator = Paginator(orders, 15)
#     page_number = request.GET.get('page', 1)
#     page = paginator.get_page(page_number)
#
#     if page.has_next():
#         next_url = f'?page={page.next_page_number()}'
#     else:
#         next_url = ''
#
#     if page.has_previous():
#         prev_url = f'?page={page.previous_page_number()}'
#     else:
#         prev_url = ''
#
#     context = {
#         'orders': page,
#         'orders_filter': orders_filter,
#         'orders_sum': orders_sum,
#         'next_url': next_url,
#         'prev_url': prev_url,
#         'current_month_revenue': current_month_revenue,
#         'orders_revenue_by_month': orders_revenue_by_month
#     }
#
#     return render(request, 'admin_revenue.html', context)
