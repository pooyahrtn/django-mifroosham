# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-16 10:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0005_transaction_confirm_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='deliver_time',
            field=models.DateTimeField(null=True),
        ),
    ]