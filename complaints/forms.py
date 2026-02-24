from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Complaint


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['description', 'department', 'urgency', 'location', 'file']