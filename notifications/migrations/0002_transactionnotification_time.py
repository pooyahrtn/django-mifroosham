# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-26 14:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactionnotification',
            name='time',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
