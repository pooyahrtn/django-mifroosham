from django.db import models
from django.contrib.auth.models import User

from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    money = models.BigIntegerField(null=True)
    # followings = models.ManyToManyField(to="self", related_name="followers", blank=True)
    avatar_url = models.ImageField(null=True, blank=True)

    def __str__(self):
        return self.user.username


class Follow(models.Model):
    followers = models.ManyToManyField(to=User, blank=True, related_name='followings')
    user = models.OneToOneField(to=User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Follow.objects.create(user=instance)
    instance.profile.save()
