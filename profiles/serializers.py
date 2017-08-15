from rest_framework import serializers
# from posts.serializers import PostWithoutSenderSerializer
from .models import Profile
from django.contrib.auth.models import User


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('avatar_url',)


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'profile')
        depth = 1



class FollowSerializers(serializers.ModelSerializer):
    following = serializers.BooleanField()
    username = serializers.CharField(read_only=True)
    profile = ProfileSerializer(read_only=True)
    requester = UserSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'profile', 'following', 'requester')
        depth = 1


