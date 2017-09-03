from django.contrib import admin
from . import models
from posts.models import Post



admin.site.register(models.Tag)