# Generated by Django 2.2.19 on 2021-05-04 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_block_user', '0002_courseblockuser_descendants'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseblockuser',
            name='processed_descendants',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]

