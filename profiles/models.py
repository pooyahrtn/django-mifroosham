from __future__ import division
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from rest_framework.authtoken.models import Token
import uuid as uuid_lib


class User(AbstractUser):
    money = models.BigIntegerField(default=0)
    qeroon = models.IntegerField(default=100)
    avatar_url = models.ImageField(null=True, blank=True)
    bio = models.CharField(max_length=400, blank=True, null=True)
    # phone_number = models.CharField(max_length=15, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    show_phone_number = models.BooleanField(default=False)
    full_name = models.CharField(null=True, max_length=40)
    score = models.FloatField(default=0, blank=True)
    count_of_rates = models.IntegerField(default=0)
    total_reposts = models.IntegerField(default=1)
    total_successful_reposts = models.IntegerField(default=1)
    count_visiting_app = models.IntegerField(default=1)

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="150" height="150" />' % self.avatar_url)

    image_tag.short_description = 'avatar'

    def __str__(self):
        return self.username


class Follow(models.Model):
    followers = models.ManyToManyField(to=User, blank=True, related_name='followings')
    user = models.OneToOneField(to=User, on_delete=models.CASCADE)
    n_followers = models.IntegerField(default=0)
    n_followings = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username


class PhoneNumber(models.Model):
    user = models.OneToOneField(User, related_name='phone_number')
    number = models.CharField(max_length=15)

    def __str__(self):
        return self.user.username


#
# class PhoneNumberConfirmationManager(models.Manager):
#     def create_confirmation(self, phone_number):
#

class PhoneNumberConfirmation(models.Model):
    user = models.OneToOneField(to=User, related_name='phone_confirmation')
    confirm_code = models.IntegerField(blank=True, null=True)
    last_request_time = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    def __str__(self):
        return self.user.username


# todo : check this.
class ReviewManager(models.Manager):
    def write_review(self, **kwargs):
        if kwargs['rate'] > 5 or kwargs['rate'] < 0:
            return

        User.objects.filter(pk=kwargs['for_user']) \
            .update(score=(F('score') * F('count_of_rates') + kwargs['rate']) / (F('count_of_rates') + 1),
                    count_of_rates=F('count_of_rates') + 1
                    )
        return self.create(**kwargs)

    def change_review(self, last_review, **kwargs):
        if kwargs['rate'] > 5 or kwargs['rate'] < 0:
            return

        User.objects.filter(pk=kwargs['for_user']) \
            .update(
            score=(F('score') * F('count_of_rates') + kwargs['rate'] - last_review.rate) / (F('count_of_rates')))
        self.filter(pk=last_review.pk).update(**kwargs)


class Review(models.Model):
    for_user = models.ForeignKey(User, related_name='reviews')
    reviewer = models.ForeignKey(User, related_name='wrote_reviews')
    rate = models.SmallIntegerField(default=5)
    comment = models.CharField(max_length=400, null=True, blank=True)
    image_url = models.ImageField(null=True, blank=True)
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)
    objects = ReviewManager()

    def __str__(self):
        return self.for_user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # instance.is_active = False
        Follow.objects.create(user=instance)
        Token.objects.create(user=instance)
        # instance.save()
