# Generated by Django 3.1.6 on 2021-02-12 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0012_auto_20190205_1711"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="event_data",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
