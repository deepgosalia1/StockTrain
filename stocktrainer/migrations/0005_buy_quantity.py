# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-04-14 20:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocktrainer', '0004_auto_20180415_0047'),
    ]

    operations = [
        migrations.AddField(
            model_name='buy',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
    ]