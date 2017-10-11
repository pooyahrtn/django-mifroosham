from django.shortcuts import render
from profiles.models import User, Profile
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from rest_framework import generics, parsers, renderers, status
from django.contrib.postgres.search import TrigramSimilarity
from profiles.serializers import UserSerializer
from posts.models import Post
from posts.serializers import SearchPostSerializer


class FindUser(generics.ListAPIView):
    lookup_field = 'username'
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.annotate(
            similarity=TrigramSimilarity('username', self.kwargs['username']),
        ).filter(similarity__gt=0.3).order_by('-similarity')
        # return User.objects.filter(username__search=self.kwargs['username'])


class FindPostTitle(generics.ListAPIView):
    lookup_field = 'title'
    serializer_class = SearchPostSerializer

    def get_queryset(self):
        query = self.kwargs['title']
        return Post.objects.annotate(
            similarity=TrigramSimilarity('title', query),
        ).filter(similarity__gt=0.5).order_by('-similarity')
