# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-14 14:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='phonenumberconfirmation',
            name='confirm_code',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]