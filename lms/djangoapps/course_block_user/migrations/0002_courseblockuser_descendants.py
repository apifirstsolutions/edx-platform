# Generated by Django 2.2.19 on 2021-05-04 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_block_user', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseblockuser',
            name='descendants',
            field=models.TextField(blank=True, null=True),
        ),
    ]

