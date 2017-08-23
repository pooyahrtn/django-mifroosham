from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    money = models.BigIntegerField(null=True)
    avatar_url = models.ImageField(null=True, blank=True)
    bio = models.CharField(max_length=400, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    show_phone_number = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Follow(models.Model):
    followers = models.ManyToManyField(to=User, blank=True, related_name='followings')
    user = models.OneToOneField(to=User, on_delete=models.CASCADE)
    n_followers = models.IntegerField(default=0)
    n_followings = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Follow.objects.create(user=instance)
        Token.objects.create(user=instance)
    instance.profile.save()
