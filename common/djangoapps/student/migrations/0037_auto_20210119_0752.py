# Generated by Django 2.2.15 on 2021-01-19 07:52

from django.db import migrations
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0036_auto_20210119_0729'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='country',
            field=django_countries.fields.CountryField(default='SG', max_length=2),
        ),
    ]
