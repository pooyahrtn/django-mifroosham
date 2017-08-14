# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-12 10:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_feed_reposter'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='like',
            name='likers',
        ),
        migrations.RemoveField(
            model_name='post',
            name='like',
        ),
        migrations.AddField(
            model_name='post',
            name='n_like',
            field=models.IntegerField(default=0),
        ),
        migrations.DeleteModel(
            name='Like',
        ),
    ]
