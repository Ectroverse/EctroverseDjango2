# Generated by Django 3.1 on 2024-02-20 15:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_auto_20240220_1510'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scouting',
            name='empire',
        ),
    ]
