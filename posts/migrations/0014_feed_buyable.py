# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-05 14:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_auto_20170904_1320'),
    ]

    operations = [
        migrations.AddField(
            model_name='feed',
            name='buyable',
            field=models.BooleanField(default=True),
        ),
    ]
