# Generated by Django 2.0.10 on 2019-06-29 13:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0012_auto_20190629_1317"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="page",
            name="meta_description",
        ),
        migrations.RemoveField(
            model_name="page",
            name="meta_keywords",
        ),
    ]
