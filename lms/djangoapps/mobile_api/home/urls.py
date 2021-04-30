"""
URLs for Mobile Home API
"""


from django.conf.urls import url

from lms.djangoapps.mobile_home_api.api import views

urlpatterns = [

    url('^mobile_home/$', views.mobile_home_page, name='mobile_home')
]
