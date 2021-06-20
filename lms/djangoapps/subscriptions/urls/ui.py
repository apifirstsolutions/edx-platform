from django.urls import path
from ..views import ui

urlpatterns = [
    path('bundled-courses/', ui.plan_list, name="plan_list"),
    path('bundled-course/<slug:slug>/', ui.plan_view, name="plan_view"),
    
    path('plan/<slug:slug>/image', ui.plan_image, name="plan_image"),
    
    path('my-bundled-courses/', ui.my_bundled_courses, name="my_bundled_courses"),
    path('my-bundled-course/<slug:slug>/',  ui.my_bundled_courses_detail, name="plan_view_tracker"),
]
