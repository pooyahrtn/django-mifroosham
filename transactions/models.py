from django.db import models
from posts.models import Post
from django.contrib.auth.models import User


class Transaction(models.Model):
    PENDING = 'pe'
    DELIVERED = 'de'
    CANCELED = 'ca'
    STATUS_CHOICES = (
        (PENDING, 'pending'),
        (DELIVERED, 'delivered'),
        (CANCELED, 'canceled')
    )

    post = models.ForeignKey(Post, on_delete=models.PROTECT)
    buyer = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        default=PENDING
    )
    confirmed = models.BooleanField(default=False)

    suspended_money = models.BigIntegerField()
    #todo: remove null = True
    time = models.DateTimeField(auto_now_add=True, null=True)
    confirm_time = models.DateTimeField(null=True)

    def __str__(self):
        return self.post.title + ' buyer: ' + self.buyer.username