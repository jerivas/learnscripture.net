# Generated by Django 2.0.10 on 2019-05-22 23:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0040_auto_20190518_1405"),
    ]

    operations = [
        migrations.AlterField(
            model_name="verseset",
            name="language_code",
            field=models.CharField(
                choices=[("en", "English"), ("tr", "Türkçe")],
                help_text="The language used in the ‘Name’, ‘Description’ and ‘Additional info’ fields.",
                max_length=2,
                verbose_name="Language",
            ),
        ),
    ]
