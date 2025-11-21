from django import forms
from django.utils import timezone
from authen.models import User, Member

class TargetModelForm(forms.ModelForm):

    class Meta:
        model = Member
        fields = (
            'target_role',
        )
        widgets = {
            'last_used': forms.DateInput(attrs={'type': 'date'}),
        }
    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)