from django.urls import path
from . import views

app_name = 'analytics_dashboard'

urlpatterns = [
    path('', views.index, name='dashboard_index'),
    path('learner/profile/', views.learner_profile_view, name='learner_profile'),
    path('admin/', views.admin_view, name='admin_dashboard'),
    path('admin/demographics/', views.demographics_view, name='admin_demographics'),
    path('admin/revenue/', views.revenue_view, name='admin_revenue'),
    path('trainer/', views.trainer_view, name='trainer_dashboard'),
    path('trainer/<course_id>/course/', views.course_detail_view, name='trainer_course_detail'),
]
