import django_filters
from django_filters import DateFilter, CharFilter, NumberFilter, ChoiceFilter, ModelChoiceFilter
# from ecommerce.models import *
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

# class OrderFilter(django_filters.FilterSet):
#     start_date = DateFilter(field_name='date_placed', lookup_expr='gte')
#     end_date = DateFilter(field_name='date_placed', lookup_expr='lte')
#     status = CharFilter(field_name='status', lookup_expr='contains')
#     price_gt = NumberFilter(field_name='total_incl_tax', lookup_expr='gt')
#
#     class Meta:
#         model = orders
#         fields = []
#
#     def __init__(self, *args, **kwargs):
#         super(OrderFilter, self).__init__(*args, **kwargs)
#         self.filters['status'].label = 'Status'
#         self.filters['price_gt'].label = 'Price Greater Than'
#         self.filters['start_date'].label = 'Date Placed Start'
#         self.filters['end_date'].label = 'Date Placed End'


class CourseFilter(django_filters.FilterSet):
    course_name = CharFilter(field_name='display_name', lookup_expr='contains')

    class Meta:
        model = CourseOverview
        fields = ['new_category', 'subcategory']

    def __init__(self, *args, **kwargs):
        super(CourseFilter, self).__init__(*args, **kwargs)
        self.filters['course_name'].label = 'Course'
        self.filters['new_category'].label = 'Category'
        self.filters['subcategory'].label = 'Sub Category'
