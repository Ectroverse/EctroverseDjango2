# Generated by Django 3.1 on 2024-05-03 13:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0028_auto_20240426_2146'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sensing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scout', models.FloatField(default=0)),
                ('empire', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.empire')),
                ('system', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.system')),
            ],
        ),
    ]
