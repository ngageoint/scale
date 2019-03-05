# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions
from django.contrib.auth.models import User
from accounts.serializers import UserAccountSerializer


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


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.

    We also ensure non-staff users are not allowed to elevate their privileges
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        # Don't allow non-staff user to upgrade themselves
        if request.data.get('is_staff', False):
            return False

        # Write permissions are only allowed to the owner of the user.
        return request.user.username == obj.username


class UserList(generics.ListCreateAPIView):
    """
    View to list all users in the system.

    * Only admin users are able to access this view.
    """
    permission_classes = (permissions.IsAdminUser,)
    queryset = User.objects.order_by('id')
    serializer_class = UserAccountSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    View to support RUD of individual user records

    * Only owner of record or admin users are allowed to edit records
    * Owners are not able to upgrade is_staff flag from false to true
    """
    permission_classes = (IsOwnerOrAdmin,)
    queryset = User.objects.all()
    serializer_class = UserAccountSerializer
