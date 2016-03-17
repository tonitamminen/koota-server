# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-03 11:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kdata', '0005_auto_20160303_1251'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='comment',
            field=models.CharField(blank=True, help_text='Any other comments to researchers (optional)', max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='device',
            name='label',
            field=models.ForeignKey(blank=True, help_text='How is this device used?  Primary means that you actively use the  device in your life, secondary is used by you sometimes. ', null=True, on_delete=django.db.models.deletion.CASCADE, to='kdata.DeviceLabel', verbose_name='Usage'),
        ),
        migrations.AlterField(
            model_name='device',
            name='name',
            field=models.CharField(help_text='A descriptive name for your device.', max_length=64),
        ),
        migrations.AlterField(
            model_name='device',
            name='type',
            field=models.CharField(choices=[('Android', 'Android'), ('PurpleRobot', 'Purple Robot (Android)'), ('Ios', 'IOS'), ('MurataBSN', 'Murata Bed Sensor')], help_text='What type of device is this?', max_length=32),
        ),
        migrations.AlterField(
            model_name='devicelabel',
            name='description',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='devicelabel',
            name='name',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]