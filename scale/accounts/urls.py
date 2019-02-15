"""Defines the URLs for the RESTful job services"""
from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views

import accounts.views as views


urlpatterns = [
    url(r'^accounts/users/$', views.GetUsers.as_view(), name='users_list_view'),
    url(r'^accounts/users/(?P<username>[\w-]+)/$', views.GetUsers.as_view(), name='get_user_view'),
    url(r'^accounts/profile/$', views.GetUser.as_view(), name='client_user_view'),

    url(r'^accounts/login/$', auth_views.login, {'template_name': 'login.html'}, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, {'template_name': 'logout.html'},  name='logout'),
    url(r'^admin/', admin.site.urls),
]