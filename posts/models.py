from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
import uuid as uuid_lib
import re
from django.utils.safestring import mark_safe


class Discount(models.Model):
    # post = models.OneToOneField(Post,on_delete=models.CASCADE)
    start_price = models.BigIntegerField()
    real_price = models.BigIntegerField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()


class Auction(models.Model):
    highest_suggest = models.BigIntegerField(blank=True, null=True)
    base_money = models.BigIntegerField(default=0)
    end_time = models.DateTimeField()


class Post(models.Model):
    NORMAL_ITEM = 0
    DISCOUNT_ITEM = 1
    AUCTION_ITEM = 2
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)
    sender = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='posts')
    sent_time = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    price = models.BigIntegerField(blank=True, null=True)
    is_charity = models.BooleanField(default=False)
    image_url = models.ImageField()
    description = models.CharField(max_length=600, blank=True)
    likes = models.ManyToManyField(to=User, blank=True, related_name='likes')
    reposters = models.ManyToManyField(to=User, blank=True, related_name='reposts')
    n_likes = models.IntegerField(default=0, editable=False)
    n_reposters = models.IntegerField(default=0, editable=False)
    discount = models.OneToOneField(Discount, on_delete=models.CASCADE, blank=True, null=True)
    auction = models.OneToOneField(Auction, on_delete=models.CASCADE, blank=True, null=True)
    disable_after_buy = models.BooleanField(default=True)
    disabled = models.BooleanField(default=False)
    deliver_time = models.IntegerField(default=24)
    confirmed_to_show = models.BooleanField(default=False)
    waiting_to_confirm = models.BooleanField(default=True, editable=False)


    def __str__(self):
        return self.title

    def get_post_type(self):
        if self.auction is not None:
            return self.AUCTION_ITEM
        elif self.discount is not None:
            return self.DISCOUNT_ITEM
        return self.NORMAL_ITEM

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="150" height="150" />' % self.image_url)

    image_tag.short_description = 'Image'


class Comment(models.Model):
    time = models.DateTimeField(auto_now_add=True, blank=True)
    text = models.CharField(max_length=400)
    user = models.ForeignKey(to=User, related_name='comments')
    post = models.ForeignKey(to=Post, on_delete=models.CASCADE, related_name='comments')


class Suggest(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='suggests')
    suggester = models.ForeignKey(User, related_name='suggests')
    suggest_to = models.ForeignKey(User, related_name='suggesteds')
    time = models.DateTimeField(auto_now_add=True)


class Feed(models.Model):
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    post = models.ForeignKey(to=Post, on_delete=models.CASCADE)
    reposter = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True, related_name='repost_posts')
    sort_time = models.DateTimeField()

    class Meta:
        ordering = ['-sort_time']


@receiver(post_save, sender=Post)
def create_new_post(sender, instance, created, **kwargs):
    if instance.confirmed_to_show and instance.waiting_to_confirm:
        instance.waiting_to_confirm = False
        pattern = re.compile("#([^\s]+)")
        m = pattern.findall(instance.description)
        from tags.models import Tag
        for tag in m:
            t, created = Tag.objects.get_or_create(name=tag, post=instance)
        instance.save()
        for user in instance.sender.follow.followers.all():
            Feed.objects.create(user=user, post=instance, sort_time=timezone.now())
