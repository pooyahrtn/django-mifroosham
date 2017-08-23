from django.db.models import Q
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from posts.models import Feed
from .models import User, Profile
from .serializers import *
from posts.serializers import UserWithPostSerializer
from rest_framework import generics
from django.db import transaction
from django.shortcuts import get_object_or_404
from .exceptions import *
from .permissions import *
from rest_framework.authtoken import views


def change_follower_feed(follower, who_followed, is_followed):
    if is_followed:
        for post in who_followed.posts.all():
            Feed.objects.create(user=follower, post=post, sort_time=post.sent_time)
    else:
        for post in who_followed.posts.all():
            Feed.objects.filter(Q(user=follower), Q(post=post) | Q(reposter=who_followed)).delete()


class FollowUser(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = FollowSerializers
    lookup_field = 'username'
    permission_classes = (permissions.IsAuthenticated, IsNotOwner)

    @transaction.atomic
    def perform_update(self, serializer):
        user = self.get_object()
        if user.pk == self.request.user.pk:
            raise FollowException(detail='you cant follow your self')
        following = user.follow.followers.filter(username=self.request.user.username).exists()
        if following:
            user.follow.followers.remove(self.request.user)
            user.follow.n_followers -= 1
            self.request.user.follow.n_followings -= 1
        else:
            user.follow.followers.add(self.request.user)
            user.follow.n_followers += 1
            self.request.user.follow.n_followings += 1
        change_follower_feed(follower=self.request.user, who_followed=user, is_followed=not following)
        self.request.user.follow.save()
        user.follow.save()
        serializer.save(following=not following, requester=self.request.user)


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserWithPostSerializer
    lookup_field = 'username'
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        if not self.request.user.is_anonymous:
            data['following'] = self.request.user.followings.filter(user=self.get_object()).exists()
        return Response(data)


class MyProfile(generics.RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = MyProfileSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOfProfile)

    def get_object(self):
        return Profile.objects.get(user=self.request.user)


class UpdateProfilePhoto(generics.UpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = UpdateProfilePhotoSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOfProfile)

    def get_object(self):
        return Profile.objects.get(user=self.request.user)


class SignUp(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = AuthenticationSerializer


class Login(views.ObtainAuthToken):
    pass









