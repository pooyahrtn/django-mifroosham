from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from django.dispatch import receiver
from django.db.models.signals import post_save


class Discount(models.Model):
    # post = models.OneToOneField(Post,on_delete=models.CASCADE)
    start_price = models.BigIntegerField()
    real_price = models.BigIntegerField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()


class Auction(models.Model):
    # post = models.OneToOneField(Post, on_delete=models.CASCADE)
    highest_suggest = models.BigIntegerField(blank=True)
    highest_suggester = models.ForeignKey(to=User, null=True, on_delete=models.SET_NULL)
    end_time = models.DateTimeField()


class Post(models.Model):
    NORMAL_ITEM = 0
    DISCOUNT_ITEM = 1
    AUCTION_ITEM = 2
    sender = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='posts')
    sent_time = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    price = models.BigIntegerField(blank=True, null=True)
    is_charity = models.BooleanField(default=False)
    image_url = models.ImageField()
    description = models.CharField(max_length=600, blank=True)
    likes = models.ManyToManyField(to=User,blank=True,related_name='likes')
    reposters = models.ManyToManyField(to=User, blank=True, related_name='reposts')
    n_likes = models.IntegerField(default=0)
    n_reposters = models.IntegerField(default=0)
    discount = models.OneToOneField(Discount, on_delete=models.CASCADE,blank=True, null=True)
    auction = models.OneToOneField(Auction, on_delete=models.CASCADE, blank=True, null=True)
    disable_after_buy = models.BooleanField(default=True)
    disabled = models.BooleanField(default=False)
    deliver_time = models.IntegerField(default=24)

    def __str__(self):
        return self.title

    def get_post_type(self):
        if self.auction is not None:
            return self.AUCTION_ITEM
        elif self.discount is not None:
            return self.DISCOUNT_ITEM
        return self.NORMAL_ITEM


class Feed(models.Model):
    # we need this because we dont want to override USER object
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    post = models.ForeignKey(to=Post, on_delete=models.CASCADE)
    reposter = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True, related_name='repost_posts')

    class Meta:
        ordering = ['-pk']


@receiver(post_save, sender=Post)
def create_new_post(sender, instance, created, **kwargs):
    if created:
        for user in instance.sender.follow.followers.all():
            Feed.objects.create(user=user, post=instance)
