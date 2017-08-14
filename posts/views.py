from rest_framework.decorators import api_view
from .models import Post, Feed
from .serializers import PostSerializer, FeedSerializer, PostWithoutSenderSerializer, LikePostSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.db import transaction
import json
from rest_framework import generics


def get_user(username):
    try:
        user = User.objects.get(username=username)
        return user
    except User.DoesNotExist:
        raise Response(status=status.HTTP_404_NOT_FOUND)


def get_user_from_pk(pk):
    try:
        user = User.objects.get(pk=pk)
        return user
    except User.DoesNotExist:
        raise Response(status=status.HTTP_404_NOT_FOUND)

# class PostList(generics.ListCreateAPIView)


class PostList(APIView):

    def get_user(self, username):
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            raise Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, username,format=None):
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

#
# class FeedList(APIView):
#
#     def get(self, request, username, format=None):
#         user = get_user(username)
#         feeds = user.feed_set.all()
#         serializer = FeedSerializer(feeds, many=True)
#         return Response(serializer.data)


class FeedList(generics.ListAPIView):
    queryset = Feed.objects.all()
    serializer_class = FeedSerializer

    def get_queryset(self):
        return self.request.user.feed_set.all()

class LikePost(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = LikePostSerializer

    @transaction.atomic
    def perform_update(self, serializer):
        post = self.get_object()
        liker = self.request.user
        liked = not post.likes.filter(pk=liker.pk).exists()
        increment = 1
        if liked:
            post.likes.add(liker)
        else:
            post.likes.remove(liker)
            increment = -1
        serializer.save(user=self.request.user, liked=liked, n_likes=post.n_likes + increment)


class SendPost(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class UserPosts(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostWithoutSenderSerializer

    def list(self, request, *args, **kwargs):
        serializer = PostWithoutSenderSerializer(self.filter_queryset(self.get_queryset()), many=True)
        return Response(serializer.data)

    def filter_queryset(self, queryset):
        # return User.objects.get(username=self.lookup_field).posts.all()
        return queryset.filter(sender__username=self.kwargs['username'])

#
# class PostDetail(generics.RetrieveAPIView):
#     queryset = Post.objects.all()
#     ser




# class UserPosts(APIView):
#     def get(self, request, username):
#         user = get_user(username=username)
#         posts = user.posts.all()
#         # i cant remember what was the following line. correct it.
#         serializer = PostSerializer(posts, many=True)
#         return Response(serializer.data)

