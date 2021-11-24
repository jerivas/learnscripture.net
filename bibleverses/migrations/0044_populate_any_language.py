# Generated by Django 2.2.4 on 2019-10-17 12:07

from django.db import migrations


def forwards(apps, schema_editor):
    from bibleverses.models import VerseSet, VerseSetType

    for vs in VerseSet.objects.filter(set_type=VerseSetType.PASSAGE):
        vs.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0043_verseset_any_language"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
