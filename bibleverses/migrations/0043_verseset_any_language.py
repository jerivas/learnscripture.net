# Generated by Django 2.2.4 on 2019-10-17 07:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0042_auto_20190713_1034"),
    ]

    operations = [
        migrations.AddField(
            model_name="verseset",
            name="any_language",
            field=models.BooleanField(default=False),
        ),
    ]
