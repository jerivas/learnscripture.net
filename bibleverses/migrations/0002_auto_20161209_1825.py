# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='verse',
            old_name='text',
            new_name='text_saved',
        ),
    ]
