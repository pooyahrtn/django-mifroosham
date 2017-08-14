from rest_framework import serializers

from posts.models import Post
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
        fields = ('id', 'username', 'profile')
        depth = 1

#
# class UserWithPostsSerializer(serializers.ModelSerializer):
#     profile = ProfileSerializer()
#     posts = serializers.PrimaryKeyRelatedField(many=True, queryset=Post.objects.all())
#
#     class Meta:
#         model = User
#         fields = '__all__'
#         depth = 1


