from collections import OrderedDict

from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from .models import Post, Feed, Comment, Suggest, ProfilePost
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
            version += 1
            self.request.user.profile.save()
        self.paginator.visit_version = version
        if page is not None:
            #todo: make it better
            pks = []
            for obj in page:
                if not obj.read:
                    pks.append(obj.pk)
            Feed.objects.filter(pk__in=pks).update(read=True, sort_version=version)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# class ReadFeeds(APIView):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def post(self, request, *args, **kwargs):
#         serializer = FeedsUUIDSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         Feed.objects.read_feeds(serializer.validated_data['uuids'], self.request.user,
#                                 serializer.validated_data['visiting_version'])
#         return Response(serializer.validated_data, status.HTTP_200_OK)


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
                Feed(user=u, post=post, reposter=self.request.user, sort_value=value, buyable=u.pk != post.sender.pk)
                for u in
                reposter.follow.followers.all())
            Feed.objects.create(user=self.request.user, post=post, reposter=self.request.user,
                                sort_value=value)
            ProfilePost.objects.create(user=self.request.user, post=post, is_repost=True)
            reposter.profile.total_reposts = F('total_reposts') + 1
            reposter.profile.save()
        else:
            post.reposters.remove(reposter)
            increment = -1
            Feed.objects.filter(user__in=self.request.user.follow.followers.all()
                                , post=post, reposter=self.request.user).delete()
            Feed.objects.filter(user=self.request.user
                                , post=post, reposter=self.request.user).delete()
            ProfilePost.objects.filter(user=self.request.user, post=post).delete()
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
    serializer_class = PostSerializer
    lookup_field = 'uuid'

    def get_object(self):
        return Post.objects.get(uuid=self.kwargs['uuid'])


class PostLikers(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        return Post.objects.get(pk=self.kwargs['pk']).likes.all()


class Comments(generics.ListAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    lookup_field = 'uuid'
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Comment.objects.filter(post__uuid=self.kwargs['uuid'])


class AddComment(APIView):
    serializer_class = BaseCommentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = get_object_or_404(Post.objects.all(), uuid=serializer.validated_data['post_uuid'])
        comment = Comment.objects.add_comment(from_user=self.request.user, text=serializer.validated_data['comment'],
                                              post=post)
        comment_serializer = CommentSerializer(comment)
        return Response(data=comment_serializer.data, status=status.HTTP_200_OK)


class DeleteComment(APIView):
    serializer_class = DeleteCommentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = get_object_or_404(Comment.objects.all(), uuid=serializer.validated_data['comment_uuid'])
        if comment.user != self.request.user:
            return Response(data='not authorized', status=status.HTTP_401_UNAUTHORIZED)
        else:
            Comment.objects.delete_comment(comment)
            return Response(data=serializer.data, status=status.HTTP_200_OK)


class SuggestPost(generics.ListCreateAPIView):
    queryset = Suggest.objects.all()
    serializer_class = SuggestSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        suggester = self.request.user
        serializer.save(suggester=suggester)

    def get_queryset(self):
        return Suggest.objects.filter(suggest_to=self.request.user)


class UserPosts(generics.ListAPIView):
    queryset = ProfilePost.objects.all()
    serializer_class = ProfilePostSerializer
    lookup_field = 'username'

    def filter_queryset(self, queryset):
        return ProfilePost.objects.filter(user__username=self.kwargs['username'])
