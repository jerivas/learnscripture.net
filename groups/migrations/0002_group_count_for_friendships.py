# Generated by Django 1.11.6 on 2018-03-06 04:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("groups", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="group",
            name="count_for_friendships",
            field=models.BooleanField(default=True),
        ),
    ]
