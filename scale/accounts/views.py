# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.contrib.auth.models import User
from accounts.serializers import UserAccountSerializer


class GetUsers(APIView):
    """
    View to list all users in the system.

    * Only admin users are able to access this view.
    """
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request, username, format=None):
        """
        Return a specific user.
        """

        return Response(User.objects.get_by_natural_key(username))

    def list(self, request, format=None):
        """
        Return a list of all users.
        """

        usernames = [user.username for user in User.objects.all()]
        return Response(usernames)


class GetUser(APIView):
    """
    View to get details on the client user.
    """

    def get(self, request, format=None):
        """
        Return details of a specific user.
        """

        serializer = UserAccountSerializer(request.user)
        return Response(serializer.data)