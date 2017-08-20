from django.shortcuts import render
from rest_framework import generics
from posts.models import Post
from .models import ReportPost
from .serializers import *
from django.shortcuts import get_object_or_404


class ReportPostView(generics.CreateAPIView):
    queryset = ReportPost.objects.all()
    serializer_class = ReportPostSerializer
