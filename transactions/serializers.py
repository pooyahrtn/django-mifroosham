from rest_framework import serializers
from posts.serializers import PostSerializer
from .models import Transaction
from profiles.serializers import UserSerializer
from django.contrib.auth.models import User


class TransactionSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    status = serializers.ReadOnlyField()
    buyer = UserSerializer(read_only=True)
    suspended_money = serializers.ReadOnlyField()

    class Meta:
        model = Transaction
        fields = '__all__'
