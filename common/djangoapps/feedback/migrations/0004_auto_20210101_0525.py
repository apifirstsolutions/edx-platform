# Generated by Django 2.2.15 on 2021-01-01 05:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0003_auto_20201211_0724'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursereview',
            name='review',
            field=models.CharField(default='No review', max_length=1000),
            preserve_default=False,
        ),
    ]
