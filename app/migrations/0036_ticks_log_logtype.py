# Generated by Django 3.1 on 2025-02-05 20:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0035_auto_20250128_1138'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticks_log',
            name='logtype',
            field=models.CharField(choices=[('t', 'Tick'), ('o', 'Operations'), ('i', 'Incantations')], default='t', max_length=1),
        ),
    ]
