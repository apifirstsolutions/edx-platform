from django.conf import settings
from django.db import models
from openedx.core.djangoapps.content.course_overviews.models import Category
from organizations.models import Organization
from datetime import datetime, date 
from django.core.exceptions import ValidationError

# Backwards compatible settings.AUTH_USER_MODEL
USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

def age_validator(date):
    dob = date
    today = date.today()
    age = ((today - dob).days)/365.25 
    if age < 18.00:
        raise ValidationError("Age can't be less than 18.")
    else:
        return date

def default_dob():
    import datetime
    dob = datetime.date(2000, 1, 1)
    return dob

class UserExtraInfo(models.Model):
    """
    This model contains two extra fields that will be saved when a user registers.
    The form that wraps this model is in the forms.py file.
    """
    user = models.OneToOneField(USER_MODEL, null=True, related_name='user_extra_info',
        on_delete=models.CASCADE)

    date_of_birth = models.DateField(verbose_name="Date of birth", validators=[age_validator], default=default_dob())

    nric = models.CharField(
        verbose_name="NRIC",
        max_length=100,
        blank=True,
        null=True
    )
    industry = models.ForeignKey(Category, related_name='users_industry', 
        on_delete=models.DO_NOTHING, default=1)
    organization = models.ForeignKey(Organization, related_name='instructor_org', 
        on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        app_label = 'custom_reg_form'
