from django.db import models
from posts.models import Post, Feed
from django.contrib.auth.models import User
import uuid as uuid_lib


class Transaction(models.Model):
    PENDING = 'pe'
    DELIVERED = 'de'
    CANCELED = 'ca'
    STATUS_CHOICES = (
        (PENDING, 'pending'),
        (DELIVERED, 'delivered'),
        (CANCELED, 'canceled')
    )
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)

    post = models.ForeignKey(Post, on_delete=models.PROTECT)
    buyer = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        default=PENDING
    )
    # confirmed = models.BooleanField(default=False)

    suspended_money = models.BigIntegerField()
    time = models.DateTimeField(auto_now_add=True)
    # confirm_time = models.DateTimeField(null=True)
    deliver_time = models.DateTimeField(null=True)
    cancel_time = models.DateTimeField(null=True)
    reposter = models.ForeignKey(to=User, null=True, blank=True, related_name='reposted_transaction')

    def __str__(self):
        return self.post.title + ' buyer: ' + self.buyer.username