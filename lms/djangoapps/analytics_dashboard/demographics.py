from datetime import date
from django.db.models import Count
from data.models import (
    CourseOverviewsCourseoverview,
    AuthUser,
    AuthUserprofile,
    StudentCourseenrollment,
    CourseOverviewsCourseoverview,
    StudentCourseaccessrole,
    CustomRegFormUserextrainfo
)


def calculate_age(born):
    today = date.today()
    try:
        birthday = born.replace(year=today.year)
    except ValueError:  # raised when birth date is February 29 and the current year is not a leap year
        birthday = born.replace(year=today.year, month=born.month + 1, day=1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


def get_learners_gender_list(user_ids):
    learners_gender = AuthUserprofile.objects.filter(user__in=user_ids).values('gender').annotate(
        total=Count('id')).order_by('-total')
    print(AuthUserprofile.objects.filter(user__in=user_ids).values('gender').annotate(total=Count('id')).order_by(
        '-total').query)
    for l in learners_gender:
        if l['gender'] == 'm':
            l['gender'] = 'Male'
            print(f'{l["gender"]} {l["total"]}')
        elif l['gender'] == 'f':
            l['gender'] = 'Female'
            print(f'{l["gender"]} {l["total"]}')
        elif l['gender'] == 'o':
            l['gender'] = 'Others'
            print(f'{l["gender"]} {l["total"]}')
        else:
            l['gender'] = 'Not set by user'
            print(f'{l["gender"]} {l["total"]}')

    learners_gender_list = []
    learners_gender_list = [value for key, value in enumerate(learners_gender) if
                            "Not set by user" not in value.values()]
    ll = [value for key, value in enumerate(learners_gender) if "Not set by user" in value.values()]

    not_set = 0
    # for l in ll:
    #     if l['gender'] == 'Not set by user':
    #         not_set += l['total']

    # learners_gender_list.append({'gender': 'Not set by user', 'total': not_set})
    # learner_gender_l["Not set by user"] = not_set
    print(f'\nFinal gender list: {learners_gender_list}')

    for x in learners_gender_list:
        print(f'{x["gender"]} {x["total"]}')

    return learners_gender_list


def get_learners_edu(user_ids):
    learners_edu = AuthUserprofile.objects.filter(user__in=user_ids).values('level_of_education').annotate(
        total=Count('id'))
    for l in learners_edu:
        if l['level_of_education'] == 'p':
            l['level_of_education'] = 'Doctorate'
        elif l['level_of_education'] == 'm':
            l['level_of_education'] = 'Master’s or professional degree'
        elif l['level_of_education'] == 'b':
            l['level_of_education'] = 'Bachelor’s degree'
        elif l['level_of_education'] == 'a':
            l['level_of_education'] = 'Associate degree'
        elif l['level_of_education'] == 'hs':
            l['level_of_education'] = 'Secondary/high school'
        elif l['level_of_education'] == 'jhs':
            l['level_of_education'] = 'Junior secondary/junior high/middle school'
        elif l['level_of_education'] == 'el':
            l['level_of_education'] = 'Elementary/primary school'
        elif l['level_of_education'] is None:
            l['level_of_education'] = 'No Formal Education'
        elif l['level_of_education'] == '':
            l['level_of_education'] = 'Diploma'

    print(f'\nLearners Edu: {learners_edu}\n')
    for l in learners_edu:
        print(f'{l["level_of_education"]} {l["total"]}')

    learners_yob = CustomRegFormUserextrainfo.objects.filter(user__in=user_ids).values()

    print(f'\nTotal Learners({len(user_ids)}):')
    print(f'\nLearners Age({learners_yob.count()}):')

    return learners_edu


def spread_age_distribution(age_list):
    age_distribution = {'<20': 0, '21 - 30': 0, '31 - 40': 0, '41 - 50': 0, '51 - 60': 0,
                        '61 - 70': 0, '>70': 0}
    print(f'\nAge list count: {len(age_list)}')
    for age in age_list:
        if age <= 20:
            age_distribution['<20'] += 1
        elif 20 < age < 30:
            age_distribution['21 - 30'] += 1
        elif 30 < age < 40:
            age_distribution['31 - 40'] += 1
        elif 40 < age < 50:
            age_distribution['41 - 50'] += 1
        elif 50 < age < 60:
            age_distribution['51 - 60'] += 1
        elif 60 < age < 70:
            age_distribution['61 - 70'] += 1
        elif age > 70:
            age_distribution['>70'] += 1
        else:
            age_distribution['Not set by user'] += 1

    return age_distribution


def median(lst):
    learners_age_without_duplicates = []
    [learners_age_without_duplicates.append(x) for x in lst if x not in learners_age_without_duplicates]
    sortedLst = sorted(learners_age_without_duplicates)
    lstLen = len(learners_age_without_duplicates)
    index = (lstLen - 1) // 2

    if (lstLen % 2):
        return sortedLst[index]
    else:
        return (sortedLst[index] + sortedLst[index + 1]) / 2.0


def age_dist(lst):
    learners_age_lte_25 = []
    [learners_age_lte_25.append(x) for x in lst if x <= 25]

    age_lte_25 = (len(learners_age_lte_25) / len(lst) * 100)

    learners_age_between_26_and_40 = []
    [learners_age_between_26_and_40.append(x) for x in lst if x > 25 and x <= 40]

    age_btw_26_and_40 = len(learners_age_between_26_and_40) / len(lst) * 100

    learners_age_gt_41 = []
    [learners_age_gt_41.append(x) for x in lst if x > 41]

    age_gt_40 = len(learners_age_gt_41) / len(lst) * 100

    dist = {'age_lte_25': round(age_lte_25, 2), 'age_btw_26_and_40': round(age_btw_26_and_40, 2),
            'age_gt_40': round(age_gt_40, 2)}

    return dist
