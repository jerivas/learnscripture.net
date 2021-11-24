# Generated by Django 2.0.10 on 2019-06-24 19:30

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations, models

import cms.models
import cms.utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ContentItem",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(blank=True, max_length=255)),
                ("content_html", cms.utils.fields.CmsHTMLField(verbose_name="Content")),
                ("protected", models.BooleanField(default=False)),
                ("metadata", django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                (
                    "template_name",
                    models.CharField(blank=True, choices=[("cms_singlecol.html", "Single column")], max_length=70),
                ),
                (
                    "used_on_pages_data",
                    django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name="used on pages"),
                ),
            ],
            options={
                "verbose_name_plural": "content items",
                "verbose_name": "content item",
            },
        ),
        migrations.CreateModel(
            name="File",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("file", models.FileField(max_length=255, upload_to=cms.models.files_directory)),
                ("title", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ("-updated",),
                "verbose_name_plural": "files",
                "verbose_name": "file",
            },
        ),
        migrations.CreateModel(
            name="Image",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("image", models.ImageField(max_length=255, upload_to=cms.models.images_directory)),
                ("title", models.CharField(max_length=255)),
                ("width", models.IntegerField(blank=True, null=True)),
                ("height", models.IntegerField(blank=True, null=True)),
            ],
            options={
                "ordering": ("-updated",),
                "verbose_name_plural": "images",
                "verbose_name": "image",
            },
        ),
        migrations.CreateModel(
            name="Page",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("meta_description", models.CharField(blank=True, max_length=255)),
                ("meta_keywords", models.CharField(blank=True, max_length=255)),
                ("title", models.CharField(max_length=255)),
                ("doc_title", models.CharField(blank=True, max_length=255)),
                ("url", models.CharField(blank=True, max_length=255)),
                ("mark_current_regexes", models.TextField(blank=True)),
                ("template_name", models.CharField(blank=True, max_length=70)),
                ("show_in_menu", models.BooleanField(default=True)),
                ("is_public", models.BooleanField(default=True)),
                ("protected", models.BooleanField(default=False)),
                ("metadata", django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ("lft", models.PositiveIntegerField(db_index=True, editable=False)),
                ("rght", models.PositiveIntegerField(db_index=True, editable=False)),
                ("tree_id", models.PositiveIntegerField(db_index=True, editable=False)),
                ("level", models.PositiveIntegerField(db_index=True, editable=False)),
            ],
            options={
                "ordering": ("tree_id", "lft"),
                "verbose_name_plural": "pages",
                "verbose_name": "page",
            },
        ),
        migrations.CreateModel(
            name="PageContentItem",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("block_name", models.CharField(max_length=255)),
                ("sort", models.IntegerField(blank=True, null=True)),
                (
                    "content_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="page_content_items",
                        to="cms.ContentItem",
                    ),
                ),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="page_content_items", to="cms.Page"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="page",
            name="content_items",
            field=models.ManyToManyField(through="cms.PageContentItem", to="cms.ContentItem"),
        ),
        migrations.AddField(
            model_name="page",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subpages",
                to="cms.Page",
                verbose_name="parent",
            ),
        ),
        migrations.AddField(
            model_name="page",
            name="redirect_page",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="redirected_pages",
                to="cms.Page",
            ),
        ),
    ]
