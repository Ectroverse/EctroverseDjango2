# Generated by Django 3.1 on 2025-01-28 10:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('galtwo', '0010_auto_20250118_0849'),
    ]

    operations = [
        migrations.AddField(
            model_name='planets',
            name='system_id',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='galtwo.system'),
        ),
    ]
