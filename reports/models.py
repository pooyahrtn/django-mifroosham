from django.db import models
from posts.models import Post
from profiles.models import User


class ReportPost(models.Model):
    post = models.ForeignKey(to=Post, on_delete=models.PROTECT, related_name='reports')
    comment = models.CharField(max_length=400, null=True, blank=True)


class ReportUser(models.Model):
    user = models.ForeignKey(to=User)
    comment = models.CharField(max_length=400, null=True, blank=True)

