from .models import UserExtraInfo
from django.forms import ModelForm
from django import forms
from openedx.core.djangoapps.content.course_overviews.models import Category

class UserExtraInfoForm(ModelForm):
    """
    The fields on this form are derived from the ExtraInfo model in models.py.
    """
    industry = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super(UserExtraInfoForm, self).__init__(*args, **kwargs)
        self.fields['nric'].error_messages = {
            #"required": u"Please tell us your NRIC.",
            "invalid": u"Not a correct NRIC.",
        }
        self.fields['industry'].error_messages = {
            "invalid": u"Not a correct Industry.",
        }

    class Meta(object):
        model = UserExtraInfo
        fields = ('nric', 'industry')
