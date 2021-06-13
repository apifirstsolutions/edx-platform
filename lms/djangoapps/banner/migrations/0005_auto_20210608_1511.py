# Generated by Django 2.2.19 on 2021-06-08 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banner', '0004_auto_20210423_0340'),
    ]

    operations = [
        migrations.AddField(
            model_name='banner',
            name='link_type',
            field=models.CharField(choices=[('about', 'ABOUT'), ('bundle', 'BUNDLE'), ('subscription', 'SUBSCRIPTION')], default='ABOUT', max_length=20),
        ),
        migrations.AddField(
            model_name='banner',
            name='link_url',
            field=models.TextField(blank=True, default=''),
        ),
    ]
