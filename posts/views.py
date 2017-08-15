from rest_framework.decorators import api_view
from .models import Post, Feed
from .serializers import PostSerializer, FeedSerializer, PostWithoutSenderSerializer, LikePostSerializer, PostDetailSerializer
from rest_framework.response import Response
from profiles.serializers import UserSerializer
from django.contrib.auth.models import User
from django.db import transaction
import json
from rest_framework import generics


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
        return queryset.filter(sender__username=self.kwargs['username'])


class PostDetail(generics.RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostDetailSerializer

    def get_object(self):
        return Post.objects.get(pk=self.kwargs['pk'])

    def retrieve(self, request, *args, **kwargs):
        serializer = PostDetailSerializer(self.get_object())
        data = serializer.data
        data['you_liked'] = self.get_object().likes.filter(username=self.request.user.username).exists()
        return Response(data)


class PostLikers(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        return Post.objects.get(pk=self.kwargs['pk']).likes.all()