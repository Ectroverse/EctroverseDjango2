# Generated by Django 3.1 on 2022-07-02 02:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_auto_20220702_0109'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Artefactimer',
        ),
        migrations.AddField(
            model_name='roundstatus',
            name='artetimer',
            field=models.IntegerField(default=1440),
        ),
    ]