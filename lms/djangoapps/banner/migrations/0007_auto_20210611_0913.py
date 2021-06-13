# Generated by Django 2.2.19 on 2021-06-11 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banner', '0006_auto_20210609_0320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='banner',
            name='link_type',
            field=models.CharField(choices=[('about', 'ABOUT'), ('bundle', 'BUNDLE'), ('subscription', 'SUBSCRIPTION'), ('external', 'EXTERNAL'), ('subcategory', 'SUBCATEGORY')], default='ABOUT', max_length=20),
        ),
    ]
