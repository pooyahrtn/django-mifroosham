from rest_framework import serializers
from .models import ReportPost


class ReportPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportPost
        fields = ('post', 'comment')
