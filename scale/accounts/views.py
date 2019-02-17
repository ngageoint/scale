# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.generics import get_object_or_404
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_403_FORBIDDEN
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, mixins, permissions
from django.contrib.auth.models import User
from accounts.serializers import UserAccountSerializer


class UserList(generics.ListCreateAPIView):
    """
    View to list all users in the system.

    * Only admin users are able to access this view.
    """
    permission_classes = (permissions.IsAdminUser,)
    queryset = User.objects.all()
    serializer_class = UserAccountSerializer


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        # Don't allow non-staff user to upgrade themselves
        if request.data.get('is_staff', False):
            return False

        # Write permissions are only allowed to the owner of the user.
        return request.user.username == obj.username


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsOwnerOrAdmin,)
    queryset = User.objects.all()
    serializer_class = UserAccountSerializer


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