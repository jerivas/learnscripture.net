# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-10 11:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_auto_20180310_1135'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='identity',
            name='new_learn_page',
        ),
    ]
