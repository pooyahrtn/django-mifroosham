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
    confirmed = serializers.BooleanField(read_only=True)
    confirm_time = serializers.ReadOnlyField()
    deliver_time = serializers.ReadOnlyField()
    cancel_time = serializers.ReadOnlyField()

    class Meta:
        model = Transaction
        fields = '__all__'


class AuctionSuggestSerializer(TransactionSerializer):
    higher_suggest = serializers.IntegerField(write_only=True)

    def create(self, validated_data):
        transaction = Transaction()
        transaction.suspended_money = validated_data.get('higher_suggest')
        return transaction
