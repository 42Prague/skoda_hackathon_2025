from django import forms
from django.utils import timezone
from authen.models import User, Member

class MemberModelForm(forms.ModelForm):
    # These fields belong to the related User model
    username = forms.CharField(max_length=50, required=True, label="Personal ID")
    first_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = Member
        fields = (
            'username', 'first_name', 'last_name', 'email', 'target_role'
        )
        widgets = {
            'last_used': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

class MemberImportForm(forms.Form):
    file = forms.FileField(
        label="Select CSV or Excel file",
        help_text="File must contain columns: first_name, last_name, email, role, primary_skill, etc."
    )