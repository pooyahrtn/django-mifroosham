from rest_framework.decorators import api_view
from .models import Post, Feed, Comment, Suggest
from .serializers import PostSerializer, FeedSerializer, PostWithoutSenderSerializer, \
    LikePostSerializer, PostDetailSerializer, RepostPostSerializer, CommentSerializer, SuggestSerializer
from rest_framework.response import Response
from profiles.serializers import UserSerializer
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import generics
from django.utils import timezone
from .permissions import *


class FeedList(generics.ListAPIView):
    queryset = Feed.objects.all()
    serializer_class = FeedSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.feed_set.filter(post__disabled=False)


class LikePost(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = LikePostSerializer
    permission_classes = (permissions.IsAuthenticated,)

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


class Repost(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = RepostPostSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def perform_update(self, serializer):
        post = self.get_object()
        reposter = self.request.user
        reposted = not post.reposters.filter(pk=reposter.pk).exists()
        increment = 1
        if reposted:
            post.reposters.add(reposter)
            for user in reposter.follow.followers.all():
                if not user.followings.filter(user=post.sender).exists():
                    Feed.objects.create(user=user, post=post, reposter=self.request.user, sort_time=timezone.now())
        else:
            post.reposters.remove(reposter)
            increment = -1
            for user in reposter.follow.followers.all():
                Feed.objects.filter(user=user, post=post, reposter=self.request.user).delete()
        serializer.save(user=self.request.user, reposted=reposted, n_reposters=post.n_reposters + increment)


class SendPost(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticated,)

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


class Comments(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        sender = self.request.user
        post = Post.objects.get(pk=self.kwargs['pk'])
        serializer.save(user=sender, post=post)


class SuggestPost(generics.ListCreateAPIView):
    queryset = Suggest.objects.all()
    serializer_class = SuggestSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        suggester = self.request.user
        serializer.save(suggester=suggester)

    def get_queryset(self):
        return Suggest.objects.filter(suggest_to=self.request.user)

