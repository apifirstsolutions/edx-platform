# Generated by Django 2.2.20 on 2021-06-17 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0005_auto_20210615_1820'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionplan',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='subscriptionplan',
            name='grace_period',
            field=models.IntegerField(default=7),
        ),
    ]
