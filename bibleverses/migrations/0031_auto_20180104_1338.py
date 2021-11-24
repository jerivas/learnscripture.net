# Generated by Django 1.11.6 on 2018-01-04 13:38

from django.db import migrations

sql = """
UPDATE bibleverses_userversestatus as UVS

SET text_order =
   (SELECT COALESCE(VERSE.gapless_bible_verse_number, VERSE.bible_verse_number)
    FROM bibleverses_verse as VERSE
    WHERE VERSE.localized_reference = UVS.localized_reference
    AND UVS.version_id = VERSE.version_id
   )

WHERE UVS.id IN
  (SELECT U0.id as id0
     FROM bibleverses_userversestatus U0
     INNER JOIN bibleverses_textversion U1
       ON (U1.id = U0.version_id)
     INNER JOIN bibleverses_verse U2
       ON (U2.localized_reference = U0.localized_reference)
          AND (U2.version_id = U0.version_id)
     WHERE U1.text_type = 'BIBLE'
  )

"""
reverse_sql = ""


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0030_auto_20180104_1210"),
    ]

    operations = [migrations.RunSQL(sql, reverse_sql)]
