# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-18 09:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_auction_base_money'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auction',
            name='highest_suggest',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]