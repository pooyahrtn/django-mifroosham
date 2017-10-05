from django.shortcuts import render
from rest_framework import generics
from posts.models import Post
from .models import ReportPost, ReportComment
from .serializers import *
from django.shortcuts import get_object_or_404
from rest_framework import permissions

class ReportPostView(generics.CreateAPIView):
    queryset = ReportPost.objects.all()
    serializer_class = ReportPostSerializer


class ReportComment(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = ReportComment.objects.all()
    serializer_class = ReportCommentSerializer

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
