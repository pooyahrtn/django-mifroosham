# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-03 14:22
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_auto_20170903_1155'),
    ]

    operations = [
        migrations.DeleteModel(
            name='FeedManager',
        ),
    ]
