# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-03 11:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_auto_20170903_1143'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='feed',
            options={'ordering': ['-read', '-not_read_sort_value', '-sort_time']},
        ),
    ]