from django.urls import path
from ..views import ui

urlpatterns = [
    path('plan/<slug:slug>/', ui.render_plan_view, {'template': 'plan_view.html'}, name="plan_view"),
]