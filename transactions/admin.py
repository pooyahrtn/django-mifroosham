from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionsAdmin(admin.ModelAdmin):
    pass
