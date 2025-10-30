from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from .models import Profile

class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'displayname', 'first_name', 'last_name', 'profession', 'location', 'interests', 'info']
        widgets = {
            'image': forms.FileInput(),
            'displayname': forms.TextInput(attrs={'placeholder': 'Add display name'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name'}),
            'profession': forms.TextInput(attrs={'placeholder': 'e.g., Software Developer, Teacher'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., New York, USA'}),
            'interests': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., Reading, Photography, Travel'}),
            'info': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Your bio (or click "Generate with AI" below)'})
        }
        labels = {
            'image': 'Profile Picture',
            'displayname': 'Display Name',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'profession': 'Profession',
            'location': 'Location',
            'interests': 'Interests (comma-separated)',
            'info': 'Bio'
        }
        
        
class EmailForm(ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email']


class UsernameForm(ModelForm):
    class Meta:
        model = User
        fields = ['username']
