# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-09 14:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0007_qeroontransaction_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qeroontransaction',
            name='cancel_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='qeroontransaction',
            name='got_time',
            field=models.DateTimeField(null=True),
        ),
    ]