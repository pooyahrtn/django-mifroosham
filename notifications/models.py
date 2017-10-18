from django.db import models
import uuid as uuid_lib
from transactions.models import Transaction
from django.conf import settings
from posts.models import Post
from . import tasks


class NotificationToken(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='notification_token')
    # todo: remove null
    token = models.UUIDField(null=True)

    def __str__(self):
        return self.user.username


class TransactionNotificationManager(models.Manager):
    def create_notification(self, transaction, user, status):
        notification = self.model(transaction=transaction, user=user, status=status)
        notification.save()
        tasks.send_notification_sms.delay(phone_number=user.phone_number.number, status=status,
                                          deliver_time=transaction.post.deliver_time)
        tasks.send_push_notification.delay(id=user.notification_token.token, status=status,
                                           title=transaction.post.title, transaction_uuid=transaction.uuid)


class TransactionNotification(models.Model):
    BUY = "bu"
    SELL = "SE"
    AUCTION = "AU"
    DELIVERED = "DE"
    AUCTION_FAILED = "AF"

    NOTIFICATION_TYPES = (
        (BUY, "buy"),
        (SELL, 'sell'),
        (AUCTION, 'auction'),
        (DELIVERED, 'delivered'),
        (AUCTION_FAILED, 'auction_failed')
    )
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)

    status = models.CharField(choices=NOTIFICATION_TYPES, max_length=2)
    transaction = models.ForeignKey(Transaction)
    read = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='transaction_notifications')
    # Todo: remove null = true
    time = models.DateTimeField(auto_now_add=True, null=True)
    objects = TransactionNotificationManager()

    def __str__(self):
        return self.transaction.post.title + ' : ' + self.user.username


class PostNotificationManager(models.Manager):
    def create_notification(self, post, requester, status):
        user = post.sender
        if requester == user:
            return
        notification = self.model(post=post, user=user, status=status)
        notification.save()
        if NotificationToken.objects.filter(user=user).exists():
            tasks.send_post_push_notification.delay(id=user.notification_token.token, status=status,
                                                    username=requester.full_name, post_uuid=post.uuid)


class PostNotification(models.Model):
    LIKE = 'li'
    SHARE = 'sh'

    NOTIFICATION_TYPES = (
        (LIKE, 'like'),
        (SHARE, 'share')
    )

    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)

    status = models.CharField(choices=NOTIFICATION_TYPES, max_length=2)
    post = models.ForeignKey(Post)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='posts_notifications')
    read = models.BooleanField(default=False)

    objects = PostNotificationManager()


class FollowNotificationManger(models.Manager):
    def create_notification(self, follower, user):
        notification = self.model(follower=follower, user=user)
        notification.save()
        if NotificationToken.objects.filter(user=user).exists():
            tasks.send_follow_push_notification.delay(id=user.notification_token.token, follower=follower.full_name)


class FollowNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='follow_notifications')
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='following_notifications')
    time = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    objects = FollowNotificationManger()

