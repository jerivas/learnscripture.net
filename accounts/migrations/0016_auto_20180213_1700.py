# Generated by Django 1.11.6 on 2018-02-13 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0015_merge_20171223_1020"),
    ]

    operations = [
        migrations.AddField(
            model_name="identity",
            name="pin_action_log_menu_large_screen",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="identity",
            name="pin_action_log_menu_small_screen",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="identity",
            name="pin_verse_options_menu_large_screen",
            field=models.BooleanField(default=False),
        ),
    ]
