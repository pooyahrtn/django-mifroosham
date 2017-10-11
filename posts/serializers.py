from rest_framework import serializers, pagination
from .models import Post, Feed, Auction, Discount, Comment, Suggest, ProfilePost
from django.contrib.auth.models import User
from profiles.serializers import UserSerializer, ProfileSerializer
import time
from django.utils import timezone
from .exceptions import *

post_fields = ('sender', 'title', 'price', 'is_charity', 'image_url_0',
               'image_url_1', 'image_url_2', 'image_url_3',
               'image_url_4', 'image_url_5', 'description',
               'discount', 'auction', 'disable_after_buy', 'deliver_time', 'ads_included',
               'sender_type', 'remaining_qeroons', 'uuid', 'sent_time', 'total_invested_qeroons', 'n_likes',
               'n_reposters', 'post_type', 'location', 'n_comments')


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

        # def create(self, validated_data):
        #      # validate_dicount_time(validated_data.get('end_time'))
        #     # super(DiscountSerializer, self).create(validated_data)
        #
        # def update(self, instance, validated_data):
        #     # validate_dicount_time(validated_data.get('end_time'))
        #     # super(DiscountSerializer, self).update(instance, validated_data)


class PostWithoutSenderSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer(allow_null=True, required=False)
    auction = AuctionSerializer(allow_null=True, required=False)
    post_type = serializers.IntegerField(source='get_post_type', read_only=True)
    # todo: remove allow null
    n_likes = serializers.IntegerField(read_only=True)
    n_reposters = serializers.IntegerField(read_only=True)
    disabled = serializers.ReadOnlyField()
    remaining_qeroons = serializers.ReadOnlyField()

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
    post_type = serializers.IntegerField(source='get_post_type', read_only=True)

    class Meta:
        model = Post
        fields = post_fields
        depth = 1


class SendPostSerializer(serializers.ModelSerializer):
    discount_start_price = serializers.IntegerField(write_only=True, allow_null=True, required=False)
    discount_end_price = serializers.IntegerField(write_only=True, allow_null=True, required=False)
    end_time = serializers.IntegerField(write_only=True, allow_null=True, required=False)
    auction_base_price = serializers.IntegerField(write_only=True, allow_null=True, required=False)
    sender_type = serializers.IntegerField(write_only=True)
    remaining_qeroons = serializers.ReadOnlyField()
    total_invested_qeroons = serializers.ReadOnlyField()
    image_url_1 = serializers.ImageField(allow_null=True, required=False)
    image_url_2 = serializers.ImageField(allow_null=True, required=False)
    image_url_3 = serializers.ImageField(allow_null=True, required=False)
    image_url_4 = serializers.ImageField(allow_null=True, required=False)
    image_url_5 = serializers.ImageField(allow_null=True, required=False)

    class Meta:
        model = Post
        fields = ('title', 'price', 'is_charity', 'image_url_0',
                  'image_url_1', 'image_url_2', 'image_url_3',
                  'image_url_4', 'image_url_5', 'description',
                  'disable_after_buy', 'deliver_time', 'ads_included',
                  'sender_type', 'remaining_qeroons', 'total_invested_qeroons',
                  'auction_base_price', 'end_time',
                  'discount_end_price', 'discount_start_price', 'location', 'next_buy_ben'
                  )

    def create(self, validated_data):
        sender_type = validated_data.pop('sender_type')
        ads_included = validated_data.get('ads_included')
        remaining_qeroons = 0
        image_count = 1
        if validated_data.get('deliver_time') < 1:
            raise SendPostException(detail='really? you will deliver it in the past?!')
        if validated_data.get('image_url_1') is not None:
            image_count += 1
            if validated_data.get('image_url_2') is not None:
                image_count += 1
                if validated_data.get('image_url_3') is not None:
                    image_count += 1
                    if validated_data.get('image_url_4') is not None:
                        image_count += 1
                        if validated_data.get('image_url_5') is not None:
                            image_count += 1
        if sender_type == 2:
            if validated_data.get('auction_base_price') is None:
                raise SendPostException(detail='auction data cant be null')
            if validated_data.get('auction_base_price') < 1000:
                raise SendPostException('low price')
            if validated_data.get('end_time') is None:
                raise SendPostException(detail='auction end time cant be null')
            if ads_included:
                remaining_qeroons = int(validated_data.get('auction_base_price') * 0.001)
            if validated_data.get('next_buy_ben') > 0.1 * validated_data.get('auction_base_price'):
                raise SendPostException(detail='too much ben')
            end_time = timezone.now() + timezone.timedelta(days=validated_data.pop('end_time'))
            auction = Auction.objects.create(base_money=validated_data.pop('auction_base_price'),
                                             end_time=end_time)
            validated_data.pop('price')
            return Post.objects.create(auction=auction, price=0, image_count=image_count,
                                       remaining_qeroons=remaining_qeroons, **validated_data)
        elif sender_type == 1:
            if validated_data.get('discount_start_price') is None:
                raise SendPostException(detail='discount data cant be null')
            if validated_data.get('discount_start_price') < 1000:
                raise SendPostException('low price')
            if validated_data.get('discount_end_price') is None:
                raise SendPostException(detail='discount data cant be null')
            if validated_data.get('end_time') is None:
                raise SendPostException(detail='discount end time cant be null')
            if ads_included:
                remaining_qeroons = int(validated_data.get('discount_start_price') * 0.001)
            if validated_data.get('next_buy_ben') > validated_data.get('discount_start_price') * 0.1:
                raise SendPostException('too much ben')
            # validate_dicount_time(validated_data.get('end_time'))
            end_time = timezone.now() + timezone.timedelta(days=validated_data.pop('end_time'))
            discount = Discount.objects.create(start_price=validated_data.pop('discount_start_price'),
                                               real_price=validated_data.pop('discount_end_price'),
                                               end_time=end_time)
            validated_data.pop('price', None)

            return Post.objects.create(discount=discount, image_count=image_count, price=0,
                                       remaining_qeroons=remaining_qeroons,
                                       **validated_data)
        else:
            if validated_data.get('price') < 1000:
                raise SendPostException(detail='low price')
            if validated_data.get('next_buy_ben') > 0.1:
                raise SendPostException('too much ben'
                                        '')
            if ads_included:
                remaining_qeroons = int(validated_data.get('price') * 0.001)
        return Post.objects.create(remaining_qeroons=remaining_qeroons, image_count=image_count, **validated_data)


class FeedSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    reposter = UserSerializer(read_only=True)
    you_liked = serializers.SerializerMethodField()
    you_reposted = serializers.SerializerMethodField()
    read = serializers.BooleanField()
    uuid = serializers.ReadOnlyField()

    class Meta:
        model = Feed
        fields = ('post', 'reposter', 'you_liked', 'you_reposted', 'uuid', 'read', 'buyable')
        depth = 1

    def get_you_liked(self, obj):
        return obj.post.likes.filter(username=self.context['request'].user.username).exists()

    def get_you_reposted(self, obj):
        return obj.post.reposters.filter(username=self.context['request'].user.username).exists()


class FeedsUUIDSerializer(serializers.Serializer):
    uuids = serializers.ListField(child=serializers.UUIDField())
    visiting_version = serializers.IntegerField()


class PostDetailSerializer(PostSerializer):
    you_liked = serializers.BooleanField(read_only=True)

    class Meta:
        model = Post
        fields = post_fields + ('you_liked', )


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    time = serializers.ReadOnlyField(read_only=True)

    class Meta:
        model = Comment
        fields = ('text', 'time', 'user', 'uuid')


class BaseCommentSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField()
    comment = serializers.CharField(max_length=400)


class DeleteCommentSerializer(serializers.Serializer):
    comment_uuid = serializers.UUIDField()


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


class ProfilePostSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    you_liked = serializers.SerializerMethodField()
    you_reposted = serializers.SerializerMethodField()

    class Meta:
        model = ProfilePost
        fields = ('is_repost', 'post', 'you_liked', 'you_reposted')

    def get_you_liked(self, obj):
        return obj.post.likes.filter(username=self.context['request'].user.username).exists()

    def get_you_reposted(self, obj):
        return obj.post.reposters.filter(username=self.context['request'].user.username).exists()


class SearchPostSerializer(PostSerializer):
    you_liked = serializers.SerializerMethodField()
    you_reposted = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = post_fields + ('you_liked', 'you_reposted')

    def get_you_liked(self, obj):
        return obj.likes.filter(username=self.context['request'].user.username).exists()

    def get_you_reposted(self, obj):
        return obj.reposters.filter(username=self.context['request'].user.username).exists()
