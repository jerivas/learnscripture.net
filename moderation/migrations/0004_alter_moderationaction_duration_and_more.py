# Generated by Django 4.1.7 on 2023-04-24 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("moderation", "0003_moderationaction_reversal_cancelled_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="moderationaction",
            name="duration",
            field=models.DurationField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name="moderationaction",
            name="reversed_at",
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
