from django.contrib import admin
from . import models
from posts.models import Comment

admin.site.register(models.ReportPost)


class CommentAdmin(admin.StackedInline):
    model = Comment


@admin.register(models.ReportComment)
class ReportCommentAdmin(admin.ModelAdmin):
    readonly_fields = ('get_comment_text',)
