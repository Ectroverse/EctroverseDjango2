from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class UploadImageForm(forms.Form):
    title = forms.CharField(max_length=50)
    image = forms.ImageField()

class RegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = ["username","email","password1","password2"]
    def clean_email(self):
        email = self.cleaned_data["email"]
        if "rightbliss" in email or 'silesia.life' in email: 
            raise ValidationError("Spam, if this is incorrect contact the Admin on Discord")
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists!")
        return email 
