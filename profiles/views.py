from django.db.models import Q
from posts.models import Feed
from .models import User
from .serializers import UserSerializer, FollowSerializers
from  posts.serializers import UserWithPostSerializer
from rest_framework import generics
from django.db import transaction
from django.shortcuts import get_object_or_404


def change_follower_feed(follower, who_followed, is_followed):
    if is_followed:
        for post in who_followed.posts.all():
            Feed.objects.create(user=follower, post=post)
    else:
        for post in who_followed.posts.all():
            Feed.objects.filter(Q(user=follower) , Q(post=post) | Q(reposter=who_followed)).delete()


class FollowUser(generics.UpdateAPIView):
    # todo: remove Anonymous users permission
    queryset = User.objects.all()
    serializer_class = FollowSerializers
    lookup_field = 'username'

    @transaction.atomic
    def perform_update(self, serializer):
        user = self.get_object()
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