# Generated by Django 2.2.15 on 2021-04-02 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0036_auto_20210402_1055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseoverview',
            name='platform_visibility',
            field=models.TextField(default='Both', null=True),
        ),
        migrations.AlterField(
            model_name='historicalcourseoverview',
            name='platform_visibility',
            field=models.TextField(default='Both', null=True),
        ),
    ]
