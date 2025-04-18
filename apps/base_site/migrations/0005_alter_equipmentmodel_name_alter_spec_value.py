# Generated by Django 5.1.7 on 2025-04-10 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base_site', '0004_specgroup_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipmentmodel',
            name='name',
            field=models.CharField(help_text='The name of the model', max_length=128),
        ),
        migrations.AlterField(
            model_name='spec',
            name='value',
            field=models.CharField(help_text='The value of the specification (e.g. 50in)', max_length=256),
        ),
    ]
