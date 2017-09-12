from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import NotificationToken, TransactionNotification
from profiles.serializers import UserSerializer
from transactions.serializers import TransactionSerializer

class UserTokenSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = NotificationToken
        fields = '__all__'

    def create(self, validated_data):
        token_object, created = NotificationToken.objects.get_or_create(user=validated_data.get('user'))
        token_object.token = validated_data.get('token')
        token_object.save()
        return token_object


class TransactionNotificationSerializer(serializers.ModelSerializer):
    transaction = TransactionSerializer(read_only=True)

    class Meta:
        model = TransactionNotification
        exclude = ('id','user')
