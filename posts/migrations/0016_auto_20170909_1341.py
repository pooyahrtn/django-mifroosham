# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-09 13:41
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0015_auto_20170907_1134'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='feed',
            options={'ordering': ['read', '-sort_version', '-sort_value', 'pk']},
        ),
        migrations.AddField(
            model_name='post',
            name='remaining_qeroons',
            field=models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]