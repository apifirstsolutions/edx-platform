# Generated by Django 2.2.20 on 2021-05-05 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_auto_20210504_1306'),
    ]

    operations = [
        migrations.AddField(
            model_name='bundle',
            name='description',
            field=models.CharField(blank=True, default=None, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='description',
            field=models.CharField(blank=True, default=None, max_length=500, null=True),
        ),
    ]
