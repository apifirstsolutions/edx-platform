
def spread_course_by_month(course_list, column_name):
    year_dist = spread_course_by_year(course_list, column_name)

    if len(course_list) > 0:
        created_year = 0
        for c in course_list:
            created_year = c[column_name].year
            created_month = c[column_name].month
            # if created_year in year_dist.keys():

            for k, v in year_dist.items():
                # print(f'{k}, {v}')
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

    # print(f'\nYear Distribution: \n{year_dist}')

    return year_dist


def spread_course_by_year(course_list, column_name):
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


def dict_fetch_all(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def spread_revenue_by_month(order_list, column_name):
    year_dist = spread_course_by_year(order_list, column_name)

    if len(order_list) > 0:
        created_year = 0
        for c in order_list:
            created_year = c[column_name].year
            created_month = c[column_name].month
            # if created_year in year_dist.keys():

            for k, v in year_dist.items():
                # print(f'{k}, {v}')
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

    # print(f'\nYear Distribution: \n{year_dist}')

    return year_dist
