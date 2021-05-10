from django.urls import path
from ..views import ui

urlpatterns = [
    path('bundle/<int:bundle_id>/', ui.render, {'template': 'bundle_view.html'}, name="single_bundle"),
]