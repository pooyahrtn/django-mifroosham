from django.db import models
import uuid as uuid_lib
from transactions.models import Transaction
from profiles.models import User
from posts.models import Post


class TransactionNotification(models.Model):
    BUY = "bu"
    SELL = "SE"
    AUCTION = "AU"
    DELIVERED = "DE"

    NOTIFICATION_TYPES = (
        (BUY, "buy"),
        (SELL, 'sell'),
        (AUCTION, 'auction'),
        (DELIVERED, 'delivered')
    )
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)

    status = models.CharField(choices=NOTIFICATION_TYPES, max_length=2)
    transaction = models.ForeignKey(Transaction)
    read = models.BooleanField(default=False)
    user = models.ForeignKey(User, related_name='transaction_notifications')


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
    user = models.ForeignKey(User, related_name='posts_notifications')
    read = models.BooleanField(default=False)
