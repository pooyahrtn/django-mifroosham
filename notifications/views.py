from django.db import transaction
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.views import APIView
from . import permissions
from . import models
from . import serializers
from rest_framework.response import Response
import requests
import json


class MyNotificationToken(generics.CreateAPIView):
    serializer_class = serializers.UserTokenSerializer
    permission_classes = (permissions.IsOwner, permissions.permissions.IsAuthenticated)
    queryset = models.NotificationToken.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GetNotifications(generics.ListAPIView):
    pass


class TransactionNotifications(generics.ListAPIView):
    permissions = (permissions.permissions.IsAuthenticated,)
    queryset = models.TransactionNotification
    serializer_class = serializers.TransactionNotificationSerializer

    def filter_queryset(self, queryset):
        return models.TransactionNotification.objects.filter(user=self.request.user)


class ReadTransactionNotifications(generics.DestroyAPIView):
    permissions = (permissions.permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        models.TransactionNotification.objects.filter(user=self.request.user).delete()
        return Response(data='deleted', status=status.HTTP_200_OK)




