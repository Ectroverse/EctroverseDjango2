# Generated by Django 3.1 on 2022-07-01 23:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_halloffame_userid'),
    ]

    operations = [
        migrations.AddField(
            model_name='halloffame',
            name='artefacts',
            field=models.IntegerField(default=0),
        ),
    ]