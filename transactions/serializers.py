from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from posts.serializers import PostSerializer
from .models import Transaction, QeroonTransaction
from profiles.serializers import UserSerializer, ReviewSerializer
from posts.models import Feed, Post
from profiles.models import User


class BuyTransactionSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(label="post_uuid")
    reposter_username = serializers.CharField(label='reposter_username', allow_null=True)

    def validate(self, attrs):
        post_uuid = attrs.get('post_uuid')
        reposter_username = attrs.get('reposter_username')
        post = get_object_or_404(Post.objects.select_for_update(), uuid=post_uuid)
        reposter = None
        if User.objects.filter(username=reposter_username).exists():
            reposter = User.objects.get(username=reposter_username)
        attrs['post'] = post
        attrs['reposter'] = reposter
        return attrs


class GetTransactionSerializer(serializers.Serializer):
    transaction_uuid = serializers.UUIDField()

    def validate(self, attrs):
        transaction_uuid = attrs.get('transaction_uuid')
        transaction = get_object_or_404(Transaction, uuid=transaction_uuid)
        attrs['transaction'] = transaction
        return attrs


class CancelSellTransactionSerializer(GetTransactionSerializer):
    disable_post = serializers.BooleanField()


class DeliverTransactionSerializer(GetTransactionSerializer):
    confirm_code = serializers.IntegerField()


class WriteReviewSerializer(GetTransactionSerializer):
    rate = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=400, allow_null=True, allow_blank=True)


class QeroonTransactionsSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    suspended_qeroon = serializers.IntegerField(read_only=True)
    requested_time = serializers.DateTimeField(read_only=True)
    got_time = serializers.DateTimeField(read_only=True)
    cancel_time = serializers.DateTimeField(read_only=True)
    post = PostSerializer(read_only=True)
    uuid = serializers.UUIDField(read_only=True)

    class Meta:
        model = QeroonTransaction
        fields = ('status', 'suspended_qeroon', 'requested_time', 'got_time', 'cancel_time', 'post', 'uuid')


class InvestOnPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(label="post_uuid")
    value = serializers.IntegerField()
    # qeroon_transaction = QeroonTransactionsSerializer(read_only=True)



transaction_base_fields = ('post', 'status', 'buyer', 'suspended_money', 'deliver_time', 'cancel_time',
                           'reposter', 'uuid', 'review', 'time', 'rate_status', 'auction_failed')


class TransactionSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    status = serializers.ReadOnlyField()
    buyer = UserSerializer(read_only=True)
    suspended_money = serializers.ReadOnlyField()
    deliver_time = serializers.ReadOnlyField()
    cancel_time = serializers.ReadOnlyField()
    reposter = UserSerializer(read_only=True)
    review = ReviewSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = transaction_base_fields


class BoughtTransactionsSerializer(TransactionSerializer):
    confirm_code = serializers.ReadOnlyField()

    class Meta:
        model = Transaction
        fields = transaction_base_fields + ('confirm_code',)


class AuctionSuggestSerializer(BuyTransactionSerializer):
    higher_suggest = serializers.IntegerField()
    #
    # def validate(self, attrs):
    #     attrs = super().validate(attrs)
    #     higher_suggest = attrs.get()



class ReturnInvestSerializer(serializers.Serializer):
    transaction_uuid = serializers.UUIDField()
    qeroons = serializers.IntegerField(read_only=True)


class GetPhoneNumberSerializer(GetTransactionSerializer):
    phone_number = serializers.CharField(required=False, max_length=20)


class TransactionPostSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = ('post',)
