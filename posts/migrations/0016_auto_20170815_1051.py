# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-15 10:51
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('posts', '0015_auto_20170815_0835'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='n_reposters',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='post',
            name='reposters',
            field=models.ManyToManyField(blank=True, related_name='reposts', to=settings.AUTH_USER_MODEL),
        ),
    ]
