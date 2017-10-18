# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-14 11:58
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FollowNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('read', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='NotificationToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PostNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ('status', models.CharField(choices=[('li', 'like'), ('sh', 'share')], max_length=2)),
                ('read', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='TransactionNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ('status', models.CharField(choices=[('bu', 'buy'), ('SE', 'sell'), ('AU', 'auction'), ('DE', 'delivered'), ('AF', 'auction_failed')], max_length=2)),
                ('read', models.BooleanField(default=False)),
                ('time', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
    ]
