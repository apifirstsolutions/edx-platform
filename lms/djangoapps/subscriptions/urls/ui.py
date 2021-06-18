from django.urls import path
from ..views import ui

urlpatterns = [
    path('plan/<slug:slug>/', ui.plan_view, name="plan_view"),
    path('my-bundled-courses/', ui.my_bundled_courses, name="my_bundled_courses"),
]
