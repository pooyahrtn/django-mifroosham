from rest_framework import serializers
from .models import Post, Feed, Auction, Discount
from django.contrib.auth.models import User
from profiles.serializers import UserSerializer, ProfileSerializer


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


class PostWithoutSenderSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer(allow_null=True)
    auction = AuctionSerializer(allow_null=True)
    post_type = serializers.IntegerField(source='get_post_type', read_only=True)
    image_url = serializers.CharField()
    n_likes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        exclude = ('sender', 'likes')
        depth = 1


class LikePostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    liked = serializers.BooleanField(read_only=True)
    title = serializers.CharField(read_only=True)
    n_likes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = ('pk', 'title', 'user', 'liked', 'n_likes')


class PostSerializer(PostWithoutSenderSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Post
        exclude = ('likes', )
        depth = 1

    def create(self, validated_data):
        auction_data = validated_data.get('auction')
        discount_data = validated_data.get('discount')
        if auction_data is not None:
            auction = Auction.objects.create(**auction_data)
            validated_data.pop('auction', None)
            return Post.objects.create(auction=auction, **validated_data)
        elif discount_data is not None:
            discount = Discount.objects.create(**discount_data)
            validated_data.pop('discount', None)
            return Post.objects.create(discount=discount, **validated_data)
        return Post.objects.create(**validated_data)


class FeedSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)

    class Meta:
        model = Feed
        fields = ('post',)
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
