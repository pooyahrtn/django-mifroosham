# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-16 10:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0004_transaction_confirmed'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='confirm_time',
            field=models.DateTimeField(null=True),
        ),
    ]
