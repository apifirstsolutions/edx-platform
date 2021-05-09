from django.urls import path
from django.conf.urls import url
from ..views.ui import render

urlpatterns = [
    # path('bundle/<int:bundle_id>/', BundleUIView, name='bundle_ui_view'),
    # path('bundle/<int:bundle_id>/', render, {'template': 'single_bundle.html'}, name="single_bundle"),
    path('bundle/<int:bundle_id>/', render, {'template': 'bundle_view.html'}, name="single_bundle"),
]