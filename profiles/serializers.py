from rest_framework import serializers
# from posts.serializers import PostWithoutSenderSerializer
from rest_framework.authtoken.models import Token

from .models import Profile
from django.contrib.auth.models import User


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = ('avatar_url', 'bio')


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'profile', 'first_name')
        depth = 1


class UserWithoutProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'first_name')


class AuthenticationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class MyProfileSerializer(serializers.ModelSerializer):
    money = serializers.ReadOnlyField()
    user = UserWithoutProfileSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = '__all__'


class UpdateProfilePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('avatar_url',)


class FollowSerializers(serializers.ModelSerializer):
    following = serializers.BooleanField(read_only=True)
    username = serializers.CharField(read_only=True)
    profile = ProfileSerializer(read_only=True)
    requester = UserSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'profile', 'following', 'requester')
        depth = 1


