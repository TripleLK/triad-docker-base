# Generated by Django 5.1.7 on 2025-05-15 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_processing', '0002_batchurlprocessingrequest_urlprocessingrequest_batch'),
    ]

    operations = [
        migrations.AddField(
            model_name='urlprocessingrequest',
            name='css_selectors',
            field=models.TextField(blank=True, help_text='Optional CSS selectors to filter HTML content (comma-separated)', null=True, verbose_name='CSS Selectors'),
        ),
    ]
