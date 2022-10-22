# Generated by Django 1.11.4 on 2017-10-18 03:58

from django.db import migrations
from parsy import regex, string

from bibleverses.languages import LANG
from bibleverses.parsing import ParsedReference, parse_validated_localized_reference


def parse_break_list(language_code, breaks, first_verse):
    """
    Parse a comma separated list of references, or raise a ValueError for failure.
    """
    # Legacy format
    legacy_break_list = (regex("[0-9]+").map(int).sep_by(string(":"), min=1, max=2)).sep_by(string(","))
    ref_list = legacy_break_list.parse(breaks)
    retval = []
    first_parsed_ref = parse_validated_localized_reference(language_code, first_verse.localized_reference)
    current_chapter = first_parsed_ref.start_chapter
    current_verse = first_parsed_ref.start_verse
    for item in ref_list:
        assert isinstance(item, list)
        if len(item) == 1:
            # Verse number
            current_verse = item[0]
        else:
            current_chapter, current_verse = item
        new_item = ParsedReference(
            language_code=language_code,
            book_name=first_parsed_ref.book_name,
            start_chapter=current_chapter,
            start_verse=current_verse,
        ).to_internal()
        retval.append(new_item)
    return retval


def forwards(apps, schema_editor):
    VerseSet = apps.get_model("bibleverses.VerseSet")
    for vs in VerseSet.objects.exclude(breaks=""):
        verse_choices = vs.verse_choices.all().order_by("set_order")
        if len(verse_choices) == 0:
            continue
        parsed_break_list = parse_break_list(LANG.EN, vs.breaks, verse_choices[0])
        new_breaks = ",".join(r.canonical_form() for r in parsed_break_list)
        vs.breaks = new_breaks
        vs.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0015_verse_merged_into"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
