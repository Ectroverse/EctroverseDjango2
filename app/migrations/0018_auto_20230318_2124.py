# Generated by Django 3.1 on 2023-03-18 21:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0017_botattack'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='system',
            name='p0',
        ),
        migrations.RemoveField(
            model_name='system',
            name='p1',
        ),
        migrations.RemoveField(
            model_name='system',
            name='p2',
        ),
        migrations.RemoveField(
            model_name='system',
            name='p3',
        ),
        migrations.RemoveField(
            model_name='system',
            name='p4',
        ),
        migrations.RemoveField(
            model_name='system',
            name='p5',
        ),
        migrations.RemoveField(
            model_name='system',
            name='p6',
        ),
        migrations.RemoveField(
            model_name='system',
            name='p7',
        ),
        migrations.AddField(
            model_name='system',
            name='img',
            field=models.CharField(blank=True, default=None, max_length=50, null=True),
        ),
    ]