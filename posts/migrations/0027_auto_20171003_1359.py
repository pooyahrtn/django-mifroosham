# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-03 13:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0026_auto_20170930_1407'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['pk']},
        ),
    ]
