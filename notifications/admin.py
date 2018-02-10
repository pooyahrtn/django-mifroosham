from django.contrib import admin
from .models import TransactionNotification, NotificationToken, PostNotification

admin.site.register(TransactionNotification)
admin.site.register(NotificationToken)
admin.site.register(PostNotification)