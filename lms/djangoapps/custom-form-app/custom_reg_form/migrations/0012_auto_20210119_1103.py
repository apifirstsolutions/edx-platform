# Generated by Django 2.2.15 on 2021-01-19 11:03

import custom_reg_form.models
import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_reg_form', '0011_auto_20210119_1049'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userextrainfo',
            name='date_of_birth',
            field=models.DateField(blank=True, default=datetime.date(2000, 1, 1), null=True, validators=[custom_reg_form.models.age_validator], verbose_name='Date of birth'),
        ),
    ]
