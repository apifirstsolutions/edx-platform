# Generated by Django 2.2.15 on 2021-01-12 10:32

import custom_reg_form.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_reg_form', '0009_auto_20210104_0623'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userextrainfo',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True, validators=[custom_reg_form.models.age_validator], verbose_name='Date of birth'),
        ),
    ]
