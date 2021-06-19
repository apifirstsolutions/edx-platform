from django.urls import path
from ..views import ui

urlpatterns = [
    path('bundled-courses/', ui.plan_list, name="plan_list"),
    path('plan/<slug:slug>/', ui.plan_view, name="plan_view"),
    path('my-bundled-courses/', ui.my_bundled_courses, name="my_bundled_courses"),
    path('my-bundled-courses/<slug:slug>/',  ui.plan_view_tracker, name="plan_view_tracker"),
]
