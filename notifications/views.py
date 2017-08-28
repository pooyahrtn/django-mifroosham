from django.shortcuts import render
from rest_framework import generics
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


class TestNotification(APIView):
    def post(self, request, *args, **kwargs):
        url = 'https://onesignal.com/api/v1/notifications'
        headers = {'Content-type': 'application/json'}

        text = 'morghe pokhte' + ' فروخته شد.'
        body = {
            "include_player_ids": [str(self.request.user.notification_token.token),],
            "app_id": "d55c41b1-3107-44f5-a9b6-49acbd1cb07f",
            "contents": {"en": text}
        }
        req = requests.post(url, json.dumps(body), headers=headers)
        return Response(req)




