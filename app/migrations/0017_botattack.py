# Generated by Django 3.1 on 2023-03-06 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_bot'),
    ]

    operations = [
        migrations.CreateModel(
            name='botattack',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user1', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('user2', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('at_type', models.CharField(blank=True, default=None, max_length=10, null=True)),
                ('time', models.IntegerField(default=15)),
            ],
        ),
    ]
