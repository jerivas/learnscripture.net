# Generated by Django 3.2.9 on 2023-02-13 11:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0060_populate_wordsuggestiondata_language_code"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="wordsuggestiondata",
            name="language_code",
        ),
    ]
