# Generated by Django 3.1 on 2024-02-20 15:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_auto_20230704_1251'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='planet',
            name='popper',
        ),
        migrations.AddField(
            model_name='roundstatus',
            name='artedelay',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='roundstatus',
            name='round_start',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='scouting',
            name='empire',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.empire'),
        ),
        migrations.AddField(
            model_name='userstatus',
            name='galsel',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='roundstatus',
            name='artetimer',
            field=models.IntegerField(default=144),
        ),
    ]