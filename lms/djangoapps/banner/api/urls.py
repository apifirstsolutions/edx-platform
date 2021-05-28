"""
URLs for banner API
"""


from django.conf.urls import url

from .views import BannerApi
from lms.djangoapps.banner.api import views

urlpatterns = [
    url('^details/$', BannerApi.as_view(), name='banner_api'),
    url('^home/$', views.mobile_home_page, name='mobile_home')
]
