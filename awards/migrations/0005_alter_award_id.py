# Generated by Django 3.2.9 on 2021-11-25 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("awards", "0004_auto_20180326_0843"),
    ]

    operations = [
        migrations.AlterField(
            model_name="award",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
    ]
