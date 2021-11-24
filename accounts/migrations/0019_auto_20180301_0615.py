# Generated by Django 1.11.6 on 2018-03-01 06:15

from django.db import migrations


def forwards(apps, schema_editor):
    Identity = apps.get_model("accounts.Identity")
    Identity.objects.update(new_learn_page=True)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0018_auto_20180301_0615"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
