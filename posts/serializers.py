from rest_framework import serializers
from .models import Post, Feed, Auction, Discount, Comment, Suggest
from django.contrib.auth.models import User
from profiles.serializers import UserSerializer, ProfileSerializer
import time
from django.utils import timezone
from .exceptions import *


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
        fields = ('highest_suggest', 'highest_suggester', 'end_time', 'base_money')


class DiscountSerializer(serializers.ModelSerializer):
    start_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Discount
        fields = ('start_price', 'real_price', 'start_time', 'end_time')

    def create(self, validated_data):
        validate_dicount_time(validated_data.get('end_time'))
        super(DiscountSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        validate_dicount_time(validated_data.get('end_time'))
        super(DiscountSerializer, self).update(instance, validated_data)


class PostWithoutSenderSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer(allow_null=True, required=False)
    auction = AuctionSerializer(allow_null=True, required=False)
    post_type = serializers.IntegerField(source='get_post_type', read_only=True)
    image_url = serializers.ImageField()
    n_likes = serializers.IntegerField(read_only=True)
    n_reposters = serializers.IntegerField(read_only=True)
    disabled = serializers.ReadOnlyField()

    class Meta:
        model = Post
        exclude = ('sender', 'likes', 'reposters', 'id', 'waiting_to_confirm', 'confirmed_to_show')
        depth = 1


class LikePostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    liked = serializers.BooleanField(read_only=True)
    title = serializers.CharField(read_only=True)
    n_likes = serializers.IntegerField(read_only=True)
    n_reposters = serializers.IntegerField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)

    class Meta:
        model = Post
        fields = ('uuid', 'title', 'user', 'liked', 'n_likes', 'n_reposters')


class RepostPostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    reposted = serializers.BooleanField(read_only=True)
    title = serializers.CharField(read_only=True)
    n_likes = serializers.IntegerField(read_only=True)
    n_reposters = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = ('uuid', 'title', 'user', 'reposted', 'n_likes', 'n_reposters')


class PostSerializer(PostWithoutSenderSerializer):
    sender = UserSerializer(read_only=True)
    sender_type = serializers.IntegerField(write_only=True)

    class Meta:
        model = Post
        exclude = ('likes', 'reposters', 'id', 'waiting_to_confirm', 'confirmed_to_show')
        depth = 1

    def create(self, validated_data):
        auction_data = validated_data.get('auction')
        discount_data = validated_data.get('discount')
        sender_type = validated_data.get('sender_type')
        validated_data.pop('sender_type', None)

        if sender_type == 2:
            if auction_data is None:
                raise SendPostException(detail='auction data cant be null')
            validate_dicount_time(discount_data.get('end_time'))
            auction = Auction.objects.create(**auction_data)
            validated_data.pop('auction', None)
            validated_data.pop('price', None)
            return Post.objects.create(auction=auction, price=0, **validated_data)
        elif sender_type == 1:
            if discount_data is None:
                raise SendPostException(detail='discount data cant be null')
            validate_dicount_time(discount_data.get('end_time'))
            discount = Discount.objects.create(**discount_data)
            validated_data.pop('discount', None)
            validated_data.pop('price', None)
            return Post.objects.create(discount=discount, price=0, **validated_data)
        else:
            if validated_data.get('price') < 1000:
                raise SendPostException(detail='low price')
        return Post.objects.create(**validated_data)

        # def update(self, instance, validated_data):
        #     sender_type = validated_data.get('sender_type')
        #     if sender_type != instance.post_type:
        #         return SendPostException('you can not change post type')
        #
        #     auction_data = validated_data.get('auction')
        #     discount_data = validated_data.get('discount')
        #
        #     if sender_type == 2:
        #         if auction_data is None:
        #             raise SendPostException(detail='auction data cant be null')
        #         auction = instance.auction
        #         Auction.objects.filter(pk=auction.pk).update(**auction_data)
        #         validated_data.pop('auction', None)
        #         return Post.objects.filter(auction=auction, **validated_data)
        #     elif sender_type == 1:
        #         if discount_data is None:
        #             raise SendPostException(detail='discount data cant be null')
        #         validate_dicount_time(discount_data.get('end_time'))
        #         discount = Discount.objects.create(**discount_data)
        #         validated_data.pop('discount', None)
        #         return Post.objects.create(discount=discount, **validated_data)


class FeedSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    reposter = UserSerializer(read_only=True)
    you_liked = serializers.SerializerMethodField()
    you_reposted = serializers.SerializerMethodField()
    sort_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Feed
        fields = ('post', 'reposter', 'you_liked', 'you_reposted', 'sort_time')
        depth = 1

    def get_you_liked(self, obj):
        return obj.post.likes.filter(username=self.context['request'].user.username).exists()

    def get_you_reposted(self, obj):
        return obj.post.reposters.filter(username=self.context['request'].user.username).exists()


class PostDetailSerializer(PostSerializer):
    you_liked = serializers.BooleanField(read_only=True)

    class Meta:
        model = Post
        exclude = ('likes', 'id', 'confirmed_to_show', 'waiting_to_confirm')


class UserWithPostSerializer(serializers.ModelSerializer):
    posts = PostWithoutSenderSerializer(read_only=True, many=True)
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('posts', 'profile', 'username')
        depth = 2


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    time = serializers.ReadOnlyField()

    class Meta:
        model = Comment
        fields = ('text', 'time', 'user')


class SuggestSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    suggester = UserSerializer(read_only=True)
    suggest_to = UserSerializer(read_only=True)
    time = serializers.ReadOnlyField()
    suggest_to_username = serializers.CharField(write_only=True)
    post_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Suggest
        fields = '__all__'

    def create(self, validated_data):
        suggested_to = User.objects.get(username=validated_data.get('suggest_to_username'))
        post = Post.objects.get(pk=validated_data.get('post_id'))
        return Suggest.objects.create(suggest_to=suggested_to, suggester=validated_data.get('suggester'), post=post)
