# Generated by Django 5.1.7 on 2025-05-16 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_processing', '0008_batchurlprocessingrequest_selector_configuration'),
    ]

    operations = [
        migrations.AddField(
            model_name='urlprocessingrequest',
            name='name',
            field=models.CharField(blank=True, help_text='Name of the processed entity', max_length=255, null=True, verbose_name='Name'),
        ),
    ]
