"""
Custom allauth adapter and form to handle extended signup fields
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.forms import SignupForm
from django import forms
from .models import Profile


class CustomSignupForm(SignupForm):
    """
    Extended signup form with additional fields
    """
    first_name = forms.CharField(
        label='First Name',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'First name',
        })
    )
    
    last_name = forms.CharField(
        label='Last Name',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Last name',
        })
    )
    
    profession = forms.CharField(
        label='Profession',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Software Developer, Teacher, Artist',
        })
    )
    
    location = forms.CharField(
        label='Location',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., New York, USA',
        })
    )
    
    interests = forms.CharField(
        label='Interests',
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'e.g., Reading, Photography, Travel, Technology',
            'rows': 2,
        })
    )
    
    def save(self, request):
        """
        Save user and store extended fields in session for the adapter
        """
        user = super().save(request)
        
        # Store extended fields in request session for adapter to retrieve
        request.session['signup_profile_data'] = {
            'first_name': self.cleaned_data.get('first_name', ''),
            'last_name': self.cleaned_data.get('last_name', ''),
            'interests': self.cleaned_data.get('interests', ''),
            'profession': self.cleaned_data.get('profession', ''),
            'location': self.cleaned_data.get('location', ''),
        }
        
        return user


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter to handle extended profile fields
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        Save user and extended profile fields during signup
        """
        # Save the user with default allauth behavior
        user = super().save_user(request, user, form, commit=False)
        
        # Get extended fields from session (stored by CustomSignupForm)
        profile_data = request.session.pop('signup_profile_data', {})
        
        if commit:
            user.save()
            # Get or create profile
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Update profile with extended fields
            for field, value in profile_data.items():
                setattr(profile, field, value)
            
            profile.save()
            
            # Note: Bio generation happens in signals.py after profile is fully saved
        
        return user

