# Generated by Django 3.1.6 on 2021-02-22 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scores", "0010_20180326_0749"),
    ]

    operations = [
        migrations.AlterField(
            model_name="actionlog",
            name="created",
            field=models.DateTimeField(db_index=True),
        ),
    ]
