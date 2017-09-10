from django.contrib import admin
from .models import Transaction, QeroonTransaction


@admin.register(Transaction)
class TransactionsAdmin(admin.ModelAdmin):
    pass


@admin.register(QeroonTransaction)
class QeroonAdmin(admin.ModelAdmin):
    pass
