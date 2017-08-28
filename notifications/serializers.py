from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import NotificationToken
from profiles.serializers import UserSerializer


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
