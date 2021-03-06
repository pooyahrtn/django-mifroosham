from django.db import transaction
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.views import APIView
from . import permissions
from . import models
from . import serializers
from rest_framework.response import Response


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

    class Meta:
        ordering = ['-pk']


class PostNotifications(generics.ListAPIView):
    queryset = models.PostNotification
    serializer_class = serializers.PostNotificationSerializer
    permission_classes = (permissions.permissions.IsAuthenticated,)
    pagination_class = None

    #  def get_queryset(self):
    #     return models.PostNotification.objects.get_unread_notifications(self.request.user).all()
    def filter_queryset(self, queryset):
        return queryset.objects.filter(user=self.request.user)


class FollowNotifications(generics.ListAPIView):
    queryset = models.FollowNotification
    serializer_class = serializers.FollowNotificationSerializer
    permission_classes = (permissions.permissions.IsAuthenticated,)
    pagination_class = None

    def filter_queryset(self, queryset):
        return queryset.objects.filter(user=self.request.user)


class ReadPostNotifications(APIView):

    def post(self, request, *args, **kwargs):
        models.PostNotification.objects.filter(user=self.request.user).delete()
        return Response('ok', status=status.HTTP_200_OK)


class ReadFollowNotifications(APIView):

    def post(self, request, *args, **kwargs):
        models.FollowNotification.objects.filter(user=self.request.user).delete()
        return Response('ok', status=status.HTTP_200_OK)


class ReadTransactionNotifications(generics.DestroyAPIView):
    permissions = (permissions.permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        models.TransactionNotification.objects.filter(user=self.request.user).delete()
        return Response(data='deleted', status=status.HTTP_200_OK)




