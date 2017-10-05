from django.shortcuts import get_object_or_404
from rest_framework import serializers
from .models import ReportPost, ReportComment
from posts.models import Comment
from .exceptions import ReportException



class ReportPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportPost
        fields = ('post', 'comment')


class ReportCommentSerializer(serializers.ModelSerializer):
    comment_uuid = serializers.UUIDField(write_only=True)

    class Meta:
        model = ReportComment
        fields = ('comment_uuid', 'status', 'text')

    def create(self, validated_data):
        comment = get_object_or_404(Comment, uuid=validated_data.pop('comment_uuid'))
        if ReportComment.objects.filter(reporter=validated_data.get('reporter'), comment=comment).exists():
            raise ReportException(detail='you already reported baby')
        return ReportComment.objects.create(comment=comment, **validated_data)

