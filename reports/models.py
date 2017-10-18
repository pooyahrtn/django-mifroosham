from django.db import models
from django.dispatch import receiver
from posts.models import Post, Comment
from django.conf import settings


class ReportPost(models.Model):
    post = models.ForeignKey(to=Post, on_delete=models.PROTECT, related_name='reports')
    comment = models.CharField(max_length=400, null=True, blank=True)


class ReportUser(models.Model):
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL)
    comment = models.CharField(max_length=400, null=True, blank=True)


class ReportComment(models.Model):
    INAPPROPRIATE = 'IP'
    INSULT = 'IN'
    SPAM = 'SP'
    OTHER = 'OT'

    STATUS_CHOICES = (
        (INAPPROPRIATE, 'inappropriate'),
        (INSULT, 'insult'),
        (SPAM, 'spam'),
        (OTHER, 'other')
    )
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reports')
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=OTHER)
    text = models.CharField(max_length=400, null=True, blank=True)
    delete_comment = models.BooleanField(default=False)

    #TODO: remove null
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)

    def __str__(self):
        return self.comment.user.username

    def get_comment_text(self):
        return self.comment.text


@receiver(models.signals.post_delete, sender=ReportComment)
def handle_delete_comment(sender, instance, **kwargs):
    if instance.delete_comment:
        Comment.objects.delete_comment(instance.comment)

