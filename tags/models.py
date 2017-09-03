from django.db import models
from posts.models import Post


class Tag(models.Model):
    name = models.CharField(max_length=60, db_index=True)
    # TODO : remove null = True
    post = models.ForeignKey(to=Post, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name
