from django.db import models
from django.db.models import F
from posts.models import Post, Feed
from django.contrib.auth.models import User
import uuid as uuid_lib
from profiles.models import Review
from datetime import datetime


class Transaction(models.Model):
    PENDING = 'pe'
    DELIVERED = 'de'
    CANCELED = 'ca'

    NOT_RATEABLE = 'nr'
    CAN_RATE = 'cr'
    RATED = 'ra'

    STATUS_CHOICES = (
        (PENDING, 'pending'),
        (DELIVERED, 'delivered'),
        (CANCELED, 'canceled')
    )

    RATE_STATUS_CHOICES = (
        (NOT_RATEABLE, 'not rateable'),
        (CAN_RATE, 'can rate'),
        (RATED, 'rated')
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
    suspended_money = models.BigIntegerField()
    time = models.DateTimeField(auto_now_add=True)
    deliver_time = models.DateTimeField(null=True)
    cancel_time = models.DateTimeField(null=True)
    reposter = models.ForeignKey(to=User, null=True, blank=True, related_name='reposted_transaction')
    confirm_code = models.IntegerField(default=0)
    rate_status = models.CharField(
        max_length=2,
        choices=RATE_STATUS_CHOICES,
        default=NOT_RATEABLE
    )
    review = models.OneToOneField(Review, blank=True, null=True, related_name='transaction')

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return self.post.title + ' buyer: ' + self.buyer.username


class QeroonTransactionManager(models.Manager):
    def give_investors_money(self, post):
        # ITS FUCKING BAD
        for transaction in self.filter(post=post, status='re').all():
            transaction.user.profile.money = F('money') + transaction.suspended_qeroon * 100
            transaction.status = QeroonTransaction.GOT
            transaction.got_time = datetime.now()
            transaction.save()
            transaction.user.profile.save()


class QeroonTransaction(models.Model):
    REQUESTED = 're'
    CANCELED = 'ca'
    GOT = 'go'
    STATUS_CHOICES = (
        (REQUESTED, 'pending'),
        (CANCELED, 'canceled'),
        (GOT, 'got')
    )
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)

    suspended_qeroon = models.IntegerField()
    requested_time = models.DateTimeField(auto_now_add=True)
    got_time = models.DateTimeField(null=True)
    cancel_time = models.DateTimeField(null=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=REQUESTED)
    post = models.ForeignKey(Post)
    # TODO: remove null= True
    user = models.ForeignKey(User, related_name='qeroon_transactions', null=True)

    objects = QeroonTransactionManager()

    def __str__(self):
        return self.user.username + ' ' + self.post.title

    class Meta:
        ordering = ['-pk',]
