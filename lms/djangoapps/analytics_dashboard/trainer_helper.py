import json
import requests

from common.djangoapps.student.views.dashboard import (
    get_org_black_and_whitelist_for_site,
    get_course_enrollments,
    get_dashboard_course_limit,
    get_filtered_course_entitlements,
)

from logging import getLogger
log = getLogger(__name__)

def str_to_datetime(date_string):
    """ Convert string date to datetime object """
    from datetime import datetime
    return datetime.strptime(date_string, '%b %d, %Y')


def dict_fetch_all(cursor):
    """ Return all rows from a cursor as a dict """
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def spread_course_by_month(course_list, column_name):
    year_dist = spread_course_by_year(course_list, column_name)

    if len(course_list) > 0:
        created_year = 0
        for c in course_list:
            created_year = c[column_name].year
            created_month = c[column_name].month

            for k, v in year_dist.items():
                if k == created_year:
                    if created_month == 1:
                        year_dist[created_year]['Jan'] += 1
                        break
                    elif created_month == 2:
                        year_dist[created_year]['Feb'] += 1
                        break
                    elif created_month == 3:
                        year_dist[created_year]['Mar'] += 1
                        break
                    elif created_month == 4:
                        year_dist[created_year]['Apr'] += 1
                        break
                    elif created_month == 5:
                        year_dist[created_year]['May'] += 1
                        break
                    elif created_month == 6:
                        year_dist[created_year]['Jun'] += 1
                        break
                    elif created_month == 7:
                        year_dist[created_year]['Jul'] += 1
                        break
                    elif created_month == 8:
                        year_dist[created_year]['Aug'] += 1
                        break
                    elif created_month == 9:
                        year_dist[created_year]['Sep'] += 1
                        break
                    elif created_month == 10:
                        year_dist[created_year]['Oct'] += 1
                        break
                    elif created_month == 11:
                        year_dist[created_year]['Nov'] += 1
                        break
                    elif created_month == 12:
                        year_dist[created_year]['Dec'] += 1
                        break
    else:
        raise ValueError()

    return year_dist


def spread_course_by_year(course_list, column_name):
    """
    Distribute courses by year

        {
            2021: ['Jan': 10, 'Feb': 30, 'Mar': 40, 'Apr': 50, 'May': 10, 'Jun': 30, 'Jul': 20, 'Aug': 20, 'Sep': 10,
                          'Oct': 80, 'Nov': 20, 'Dec': 10,]
            2020: ['Jan': 80, 'Feb': 40, 'Mar': 60, 'Apr': 60, 'May': 70, 'Jun': 20, 'Jul': 0, 'Aug': 0, 'Sep': 0,
                          'Oct': 0, 'Nov': 0, 'Dec': 0,]
        }
    """
    month_distribution = {'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0, 'May': 0, 'Jun': 0, 'Jul': 0, 'Aug': 0, 'Sep': 0,
                          'Oct': 0, 'Nov': 0, 'Dec': 0, }

    lst = []
    [lst.append(c[column_name].year) for c in course_list if c[column_name].year not in lst]
    lst.sort(reverse=True)
    year_dist = {}
    for l in lst:
        year_dist[l] = {'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0, 'May': 0, 'Jun': 0, 'Jul': 0, 'Aug': 0, 'Sep': 0,
                        'Oct': 0, 'Nov': 0, 'Dec': 0, }
    return year_dist


def spread_revenue_by_year(course_list, column_name):
    """
    Distribute revenue by year

        {
            2021: ['Jan': 10, 'Feb': 30, 'Mar': 40, 'Apr': 50, 'May': 10, 'Jun': 30, 'Jul': 20, 'Aug': 20, 'Sep': 10,
                          'Oct': 80, 'Nov': 20, 'Dec': 10,]
            2020: ['Jan': 80, 'Feb': 40, 'Mar': 60, 'Apr': 60, 'May': 70, 'Jun': 20, 'Jul': 0, 'Aug': 0, 'Sep': 0,
                          'Oct': 0, 'Nov': 0, 'Dec': 0,]
        }
    """

    month_distribution = {'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0, 'May': 0, 'Jun': 0, 'Jul': 0, 'Aug': 0, 'Sep': 0,
                          'Oct': 0, 'Nov': 0, 'Dec': 0, }

    lst = []
    for c in course_list:
        if str_to_datetime(c[column_name]).year not in lst:
            lst.append(str_to_datetime(c[column_name]).year)

    lst.sort(reverse=True)
    year_dist = {}
    for l in lst:
        year_dist[l] = {'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0, 'May': 0, 'Jun': 0, 'Jul': 0, 'Aug': 0, 'Sep': 0,
                        'Oct': 0, 'Nov': 0, 'Dec': 0, }
    return year_dist


def spread_revenue_by_month(order_list, column_name):
    """
    Distribute revenue by month

    ['Jan': 10, 'Feb': 30, 'Mar': 40, 'Apr': 50, 'May': 10, 'Jun': 30, 'Jul': 20, 'Aug': 20, 'Sep': 10,
                'Oct': 80, 'Nov': 20, 'Dec': 10,]
     """
    year_dist = spread_course_by_year(order_list, column_name)

    if len(order_list) > 0:
        created_year = 0
        for c in order_list:
            created_year = c[column_name].year
            created_month = c[column_name].month

            for k, v in year_dist.items():
                if k == created_year:
                    if created_month == 1:
                        year_dist[created_year]['Jan'] += c['total_incl_tax']
                        break
                    elif created_month == 2:
                        year_dist[created_year]['Feb'] += c['total_incl_tax']
                        break
                    elif created_month == 3:
                        year_dist[created_year]['Mar'] += c['total_incl_tax']
                        break
                    elif created_month == 4:
                        year_dist[created_year]['Apr'] += c['total_incl_tax']
                        break
                    elif created_month == 5:
                        year_dist[created_year]['May'] += c['total_incl_tax']
                        break
                    elif created_month == 6:
                        year_dist[created_year]['Jun'] += c['total_incl_tax']
                        break
                    elif created_month == 7:
                        year_dist[created_year]['Jul'] += c['total_incl_tax']
                        break
                    elif created_month == 8:
                        year_dist[created_year]['Aug'] += c['total_incl_tax']
                        break
                    elif created_month == 9:
                        year_dist[created_year]['Sep'] += c['total_incl_tax']
                        break
                    elif created_month == 10:
                        year_dist[created_year]['Oct'] += c['total_incl_tax']
                        break
                    elif created_month == 11:
                        year_dist[created_year]['Nov'] += c['total_incl_tax']
                        break
                    elif created_month == 12:
                        year_dist[created_year]['Dec'] += c['total_incl_tax']
                        break
    else:
        raise ValueError()

    return year_dist


def spread_revenue_by_month_from_orders_api(order_list, column_name):
    """
    Distribute revenue by month

    ['Jan': 10, 'Feb': 30, 'Mar': 40, 'Apr': 50, 'May': 10, 'Jun': 30, 'Jul': 20, 'Aug': 20, 'Sep': 10,
                'Oct': 80, 'Nov': 20, 'Dec': 10,]
     """
    year_dist = spread_revenue_by_year(order_list, column_name)

    if len(order_list) > 0:
        created_year = 0
        for c in order_list:
            created_year = str_to_datetime(c[column_name]).year
            created_month = str_to_datetime(c[column_name]).month

            for k, v in year_dist.items():
                if k == created_year:
                    if created_month == 1:
                        year_dist[created_year]['Jan'] += float(c['price'])
                        break
                    elif created_month == 2:
                        year_dist[created_year]['Feb'] += float(c['price'])
                        break
                    elif created_month == 3:
                        year_dist[created_year]['Mar'] += float(c['price'])
                        break
                    elif created_month == 4:
                        year_dist[created_year]['Apr'] += float(c['price'])
                        break
                    elif created_month == 5:
                        year_dist[created_year]['May'] += float(c['price'])
                        break
                    elif created_month == 6:
                        year_dist[created_year]['Jun'] += float(c['price'])
                        break
                    elif created_month == 7:
                        year_dist[created_year]['Jul'] += float(c['price'])
                        break
                    elif created_month == 8:
                        year_dist[created_year]['Aug'] += float(c['price'])
                        break
                    elif created_month == 9:
                        year_dist[created_year]['Sep'] += float(c['price'])
                        break
                    elif created_month == 10:
                        year_dist[created_year]['Oct'] += float(c['price'])
                        break
                    elif created_month == 11:
                        year_dist[created_year]['Nov'] += float(c['price'])
                        break
                    elif created_month == 12:
                        year_dist[created_year]['Dec'] += float(c['price'])
                        break
    else:
        raise ValueError()

    return year_dist


def get_orders_details(request):
    """Get order details from the oscar to show in the admin dashboard """

    host = request.get_host()
    if "dev" in host:
        host = "edx-dev.lhubsg.com"
    log.info(f"host: {host}")

    data = {'client_id': 'qRLaOgG6vKSbptr9qoGAdZWkCtSWikeTdM5vBPdX',
            'username': 'tonytest',
            'password': 'edx',
            'grant_type': 'password',
            'token_type': 'bearer'}

    oauth_response = requests.post(
        url='http://' + host + '/oauth2/access_token', data=data)
    json_response = json.loads(oauth_response.text)

    if "access_token" in json_response.keys():
        jwt_token = json_response['access_token']
        headers = {'Authorization': 'BEARER ' + jwt_token}
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'
        headers['User-Agent'] = user_agent
        URL = 'http://' + host + '/lhub_extended_api/orderlist'
        response = requests.get(url=URL, headers=headers)

    return response.json()


def get_course_enrollment(request, user):
    """
    Get Course enrollments for the the user
    """

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


def orders_by_quarter(order_by_month, quarter=None):
    first_quarter = ['Jan', 'Feb', 'Mar']
    second_quarter = ['Apr', 'May', 'Jun']
    third_quarter = ['Jul', 'Aug', 'Sep']
    fourth_quarter = ['Oct', 'Nov', 'Dec']

    for year, data in order_by_month.copy().items():
        for k in data.copy().keys():
            if quarter == 1:
                if k not in first_quarter:
                    del data[k]
            elif quarter == 2:
                if k not in second_quarter:
                    del data[k]
            elif quarter == 3:
                if k not in third_quarter:
                    del data[k]
            elif quarter == 4:
                if k not in fourth_quarter:
                    del data[k]
            else:
                pass

    return order_by_month
