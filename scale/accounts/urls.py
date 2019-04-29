from __future__ import unicode_literals

from django.conf.urls import url

import accounts.views as views


urlpatterns = [
    url(r'^accounts/users/$', views.UserList.as_view(), name='users_list_view'),
    url(r'^accounts/users/(?P<pk>[\w-]+)/$', views.UserDetail.as_view(), name='user_detail_view'),
    url(r'^accounts/profile/$', views.GetUser.as_view(), name='current_user_view'),
]
