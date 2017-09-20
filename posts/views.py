from collections import OrderedDict

from django.db.models import F
from rest_framework.views import APIView
from .models import Post, Feed, Comment, Suggest
from .serializers import *
from rest_framework.response import Response
from profiles.serializers import UserSerializer
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import generics, status
from django.utils import timezone
from .permissions import *
from .utils import value_of_feed
from rest_framework.pagination import PageNumberPagination


class FeedPaginator(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('visit_version', self.visit_version),
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class FeedList(generics.ListAPIView):
    queryset = Feed.objects.all()
    serializer_class = FeedSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = FeedPaginator

    def get_queryset(self):
        return self.request.user.feed_set.filter(post__disabled=False)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        version = self.request.user.profile.count_visiting_app

        if request.GET.get('page') is None:
            self.request.user.profile.count_visiting_app += 1
            self.request.user.profile.save()
        self.paginator.visit_version = version
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ReadFeeds(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = FeedsUUIDSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        Feed.objects.read_feeds(serializer.validated_data['uuids'], self.request.user,
                                serializer.validated_data['visiting_version'])
        return Response(serializer.validated_data, status.HTTP_200_OK)


class LikePost(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = LikePostSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'uuid'

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
    lookup_field = 'uuid'

    @transaction.atomic
    def perform_update(self, serializer):
        post = self.get_object()
        reposter = self.request.user
        reposted = not post.reposters.filter(pk=reposter.pk).exists()
        if post.sender.id == reposter.pk:
            raise ShareException()
        increment = 1
        if reposted:
            post.reposters.add(reposter)
            value = value_of_feed(post.sender.profile.score, post.sender.profile.count_of_rates,
                                  reposter.profile.total_successful_reposts / reposter.profile.total_reposts)

            Feed.objects.bulk_create(
                Feed(user=u, post=post, reposter=self.request.user, sort_value=value) for u in
                reposter.follow.followers.all())
            Feed.objects.create(user=self.request.user, post=post, reposter=self.request.user,
                                sort_value=value)
            reposter.profile.total_reposts = F('total_reposts') + 1
            reposter.profile.save()
        else:
            post.reposters.remove(reposter)
            increment = -1
            Feed.objects.filter(user__in=self.request.user.follow.followers.all()
                                , post=post, reposter=self.request.user).delete()
            Feed.objects.filter(user=self.request.user
                                , post=post, reposter=self.request.user).delete()
            reposter.profile.total_reposts = F('total_reposts') - 1
            reposter.profile.save()
        serializer.save(user=self.request.user, reposted=reposted, n_reposters=post.n_reposters + increment)


class SendPost(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = SendPostSerializer
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
    lookup_field = 'uuid'

    def get_object(self):
        return Post.objects.get(uuid=self.kwargs['uuid'])

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
