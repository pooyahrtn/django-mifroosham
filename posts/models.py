from django.db import models
from django.db.models import F
import uuid as uuid_lib
from django.utils.safestring import mark_safe
from django.conf import settings


class Discount(models.Model):
    # post = models.OneToOneField(Post,on_delete=models.CASCADE)
    start_price = models.BigIntegerField(blank=True)
    real_price = models.BigIntegerField(blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True)


class Auction(models.Model):
    highest_suggest = models.BigIntegerField(blank=True, null=True)
    base_money = models.BigIntegerField(default=0)
    end_time = models.DateTimeField(blank=True)


class Post(models.Model):
    NORMAL_ITEM = 0
    DISCOUNT_ITEM = 1
    AUCTION_ITEM = 2
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)
    sender = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    sent_time = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    price = models.BigIntegerField(blank=True, null=True)
    is_charity = models.BooleanField(default=False)
    # TODO:remove this null
    image_url_0 = models.ImageField(null=True, blank=True)
    image_url_1 = models.ImageField(null=True, blank=True)
    image_url_2 = models.ImageField(null=True, blank=True)
    image_url_3 = models.ImageField(null=True, blank=True)
    image_url_4 = models.ImageField(null=True, blank=True)
    image_url_5 = models.ImageField(null=True, blank=True)
    image_count = models.SmallIntegerField(default=1)
    description = models.CharField(max_length=600, blank=True)
    likes = models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True, related_name='likes')
    reposters = models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True, related_name='reposts')
    n_likes = models.IntegerField(default=0, editable=False)
    n_reposters = models.IntegerField(default=0, editable=False)
    n_comments = models.IntegerField(default=0, editable=False)
    discount = models.OneToOneField(Discount, on_delete=models.CASCADE, blank=True, null=True)
    auction = models.OneToOneField(Auction, on_delete=models.CASCADE, blank=True, null=True)
    disable_after_buy = models.BooleanField(default=True)
    disabled = models.BooleanField(default=False)
    deliver_time = models.IntegerField(default=2)
    confirmed_to_show = models.BooleanField(default=False)
    waiting_to_confirm = models.BooleanField(default=True, editable=False)
    remaining_qeroons = models.PositiveIntegerField(default=0)
    total_invested_qeroons = models.PositiveIntegerField(default=0)
    ads_included = models.BooleanField(default=False)
    location = models.CharField(max_length=14, null=True, blank=True)
    next_buy_ben = models.BigIntegerField(default=0, blank=True)

    def __str__(self):
        return self.title

    def get_post_type(self):
        if self.auction is not None:
            return self.AUCTION_ITEM
        elif self.discount is not None:
            return self.DISCOUNT_ITEM
        return self.NORMAL_ITEM

    def image_tag_0(self):
        return mark_safe('<img src="/media/%s" width="150" height="150" />' % self.image_url_0)

    def image_tag_1(self):
        return mark_safe('<img src="/media/%s" width="150" height="150" />' % self.image_url_1)

    def image_tag_2(self):
        return mark_safe('<img src="/media/%s" width="150" height="150" />' % self.image_url_2)

    def image_tag_3(self):
        return mark_safe('<img src="/media/%s" width="150" height="150" />' % self.image_url_3)

    def image_tag_4(self):
        return mark_safe('<img src="/media/%s" width="150" height="150" />' % self.image_url_4)

    def image_tag_5(self):
        return mark_safe('<img src="/media/%s" width="150" height="150" />' % self.image_url_5)


class CommentManager(models.Manager):
    def add_comment(self, from_user, text, post):
        Post.objects.filter(pk=post.pk).update(n_comments=F('n_comments') + 1)
        return self.create(user=from_user, text=text, post=post)

    def delete_comment(self, comment):
        self.get(pk=comment.pk).delete()
        Post.objects.filter(pk=comment.post.pk).update(n_comments=F('n_comments') - 1)


class Comment(models.Model):
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)
    time = models.DateTimeField(auto_now_add=True, blank=True)
    text = models.CharField(max_length=400)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='comments')
    post = models.ForeignKey(to=Post, on_delete=models.CASCADE, related_name='comments')

    objects = CommentManager()

    def __str__(self):
        return self.post.title

    class Meta:
        ordering = ['pk',]


class Suggest(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='suggests')
    suggester = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='suggests')
    suggest_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='suggesteds')
    time = models.DateTimeField(auto_now_add=True)


# class FeedManager(models.Manager):
#     def read_feeds(self, feeds_uuids, user, viewing_version):
#         self.filter(uuid__in=feeds_uuids, user=user, read=False).update(read=True, sort_version=viewing_version)


class Feed(models.Model):
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(to=Post, on_delete=models.CASCADE)
    reposter = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='repost_posts')
    sort_version = models.IntegerField(default=0, blank=True, db_index=True)
    sort_value = models.IntegerField(default=0, db_index=True)
    read = models.BooleanField(default=False)
    buyable = models.BooleanField(default=True)
    # objects = FeedManager()

    def __str__(self):
        return self.post.title

    class Meta:
        ordering = ['read', '-sort_version', '-sort_value', '-pk']


class ProfilePost(models.Model):
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    is_repost = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username + ' : ' + self.post.title

    class Meta:
        ordering = ['-pk']
