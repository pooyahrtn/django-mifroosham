# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-31 14:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_post_confirmed_to_show'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='waiting_to_confirm',
            field=models.BooleanField(default=True),
        ),
    ]