# Generated by Django 1.11.6 on 2017-11-30 10:16

from django.db import migrations


def forwards(apps, schema_editor):
    Identity = apps.get_model("accounts.Identity")
    Identity.objects.filter(desktop_testing_method="0").update(desktop_testing_method="FULL_WORDS")
    Identity.objects.filter(desktop_testing_method="1").update(desktop_testing_method="FIRST_LETTER")
    Identity.objects.filter(desktop_testing_method="2").update(desktop_testing_method="ON_SCREEN")
    Identity.objects.filter(touchscreen_testing_method="0").update(touchscreen_testing_method="FULL_WORDS")
    Identity.objects.filter(touchscreen_testing_method="1").update(touchscreen_testing_method="FIRST_LETTER")
    Identity.objects.filter(touchscreen_testing_method="2").update(touchscreen_testing_method="ON_SCREEN")


def backwards(apps, schema_editor):
    Identity = apps.get_model("accounts.Identity")
    Identity.objects.filter(desktop_testing_method="FULL_WORDS").update(desktop_testing_method="0")
    Identity.objects.filter(desktop_testing_method="FIRST_LETTER").update(desktop_testing_method="1")
    Identity.objects.filter(desktop_testing_method="ON_SCREEN").update(desktop_testing_method="2")
    Identity.objects.filter(touchscreen_testing_method="FULL_WORDS").update(touchscreen_testing_method="0")
    Identity.objects.filter(touchscreen_testing_method="FIRST_LETTER").update(touchscreen_testing_method="1")
    Identity.objects.filter(touchscreen_testing_method="ON_SCREEN").update(touchscreen_testing_method="2")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0012_auto_20171130_1009"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
