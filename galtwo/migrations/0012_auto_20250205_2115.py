# Generated by Django 3.1 on 2025-02-05 21:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('galtwo', '0011_planets_system_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='planets',
            old_name='system_id',
            new_name='system',
        ),
    ]
