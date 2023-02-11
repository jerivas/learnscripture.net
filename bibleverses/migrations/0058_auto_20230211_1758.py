# Generated by Django 3.2.9 on 2023-02-11 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0057_fix_mezmurlar_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="textversion",
            name="language_code",
            field=models.CharField(
                choices=[("en", "English"), ("nl", "Nederlands"), ("tr", "Türkçe"), ("es", "Español")],
                default="en",
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name="verseset",
            name="language_code",
            field=models.CharField(
                choices=[("en", "English"), ("nl", "Nederlands"), ("tr", "Türkçe"), ("es", "Español")],
                help_text="The language used in the ‘Name’, ‘Description’ and ‘Additional info’ fields.",
                max_length=2,
                verbose_name="Language",
            ),
        ),
    ]
