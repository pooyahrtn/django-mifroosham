# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-23 14:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0014_auto_20170923_1247'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='auction_failed',
            field=models.BooleanField(default=False),
        ),
    ]