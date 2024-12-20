# Generated by Django 3.1 on 2023-07-04 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0019_auto_20230704_1248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mapsettings',
            name='map_setting',
            field=models.CharField(choices=[('UE', 'Unexplored planets'), ('PE', 'Planets of empire'), ('PF', 'Planets of faction '), ('YE', 'Your empire'), ('YR', 'Your portals'), ('YP', 'Your planets'), ('SC', 'Scouted Planets')], default='UE', max_length=2),
        ),
    ]
