# Generated by Django 2.0.10 on 2019-06-29 11:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0005_auto_20190627_1112"),
    ]

    operations = [
        migrations.RunSQL(
            "DROP TABLE IF EXISTS fiber_contentitem, fiber_file, fiber_image, fiber_page, fiber_pagecontentitem CASCADE;"
            "",
            hints={"target_dbs": ["default"]},
        )
    ]
