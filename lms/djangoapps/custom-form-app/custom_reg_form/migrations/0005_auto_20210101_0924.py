# Generated by Django 2.2.15 on 2021-01-01 09:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('custom_reg_form', '0004_auto_20201228_0522'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userextrainfo',
            name='industry',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, related_name='users_industry', to='course_overviews.Category'),
            preserve_default=False,
        ),
    ]
