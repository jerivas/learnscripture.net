# Generated by Django 4.1.7 on 2023-04-23 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("moderation", "0002_moderationaction_duration_moderationaction_user_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="moderationaction",
            name="reversal_cancelled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="moderationaction",
            name="reversed_at",
            field=models.DateTimeField(default=None, null=True),
        ),
    ]
