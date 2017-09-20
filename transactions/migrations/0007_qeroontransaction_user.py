# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-09 14:20
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('transactions', '0006_qeroontransaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='qeroontransaction',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='qeroon_transactions', to=settings.AUTH_USER_MODEL),
        ),
    ]