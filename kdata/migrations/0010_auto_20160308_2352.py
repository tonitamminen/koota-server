# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-08 21:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kdata', '0009_surveytoken_persistent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='surveytoken',
            name='admin_note',
        ),
        migrations.AlterField(
            model_name='surveytoken',
            name='data',
            field=models.CharField(blank=True, max_length=256),
        ),
    ]
