# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-18 15:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_auto_20171014_1426'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='total_reposts',
            field=models.IntegerField(default=1),
        ),
    ]
