from rest_framework import serializers
from .models import Post, Feed, Auction, Discount
from django.contrib.auth.models import User
from profiles.serializers import UserSerializer, ProfileSerializer
import time
from django.utils import timezone


def validate_dicount_time(end_time):
    less = int(time.mktime(timezone.now().timetuple()))
    greater = int(time.mktime(end_time.timetuple()))
    if less > greater:
        raise serializers.ValidationError('end_time is greater than now')


class AuctionSerializer(serializers.ModelSerializer):
    highest_suggest = serializers.IntegerField(read_only=True)
    highest_suggester = UserSerializer(read_only=True)

    class Meta:
        model = Auction
        fields = ('highest_suggest', 'highest_suggester', 'end_time')


class DiscountSerializer(serializers.ModelSerializer):
    start_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Discount
        fields = ('start_price', 'real_price', 'start_time', 'end_time')

    def create(self, validated_data):
        validate_dicount_time( validated_data.get('end_time'))
        super(DiscountSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        validate_dicount_time(validated_data.get('end_time'))
        super(DiscountSerializer, self).update(instance, validated_data)


class PostWithoutSenderSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer(allow_null=True)
    auction = AuctionSerializer(allow_null=True)
    post_type = serializers.IntegerField(source='get_post_type', read_only=True)
    image_url = serializers.CharField()
    n_likes = serializers.IntegerField(read_only=True)
    n_reposters = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        exclude = ('sender', 'likes', 'reposters')
        depth = 1


class LikePostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    liked = serializers.BooleanField(read_only=True)
    title = serializers.CharField(read_only=True)
    n_likes = serializers.IntegerField(read_only=True)
    n_reposters = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = ('pk', 'title', 'user', 'liked', 'n_likes','n_reposters')


class RepostPostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    reposted = serializers.BooleanField(read_only=True)
    title = serializers.CharField(read_only=True)
    n_likes = serializers.IntegerField(read_only=True)
    n_reposters = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = ('pk', 'title', 'user', 'reposted', 'n_likes','n_reposters')


class PostSerializer(PostWithoutSenderSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Post
        exclude = ('likes', 'reposters')
        depth = 1

    def create(self, validated_data):
        auction_data = validated_data.get('auction')
        discount_data = validated_data.get('discount')
        if auction_data is not None:
            auction = Auction.objects.create(**auction_data)
            validated_data.pop('auction', None)
            return Post.objects.create(auction=auction, **validated_data)
        elif discount_data is not None:
            validate_dicount_time(discount_data.get('end_time'))
            discount = Discount.objects.create(**discount_data)
            validated_data.pop('discount', None)
            return Post.objects.create(discount=discount, **validated_data)
        return Post.objects.create(**validated_data)


class FeedSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    reposter = UserSerializer(read_only=True)

    class Meta:
        model = Feed
        fields = ('post','reposter')
        depth = 1


class PostDetailSerializer(PostSerializer):
    you_liked = serializers.BooleanField(read_only=True)

    class Meta:
        model = Post
        exclude = ('likes',)


class UserWithPostSerializer(serializers.ModelSerializer):
    posts = PostWithoutSenderSerializer(read_only=True, many=True)
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('posts', 'profile','username')
        depth = 2
