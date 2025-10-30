from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import MoodEntry, Habit


class MoodEntryForm(forms.ModelForm):
    """Form for creating and editing mood entries"""
    
    class Meta:
        model = MoodEntry
        fields = ['mood_level', 'mood_label', 'notes', 'date']
        widgets = {
            'mood_level': forms.RadioSelect(attrs={
                'class': 'form-radio text-blue-600 focus:ring-blue-500'
            }),
            'mood_label': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Optional notes about your mood...'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set default date to today if not provided
        if not self.instance.pk and not self.initial.get('date'):
            self.fields['date'].initial = timezone.now().date()
        
        # Add custom labels and help text
        self.fields['mood_level'].label = 'How are you feeling today?'
        self.fields['mood_level'].help_text = 'Select a number from 1 (Very Low) to 5 (Excellent)'
        self.fields['mood_label'].label = 'Mood Description'
        self.fields['mood_label'].help_text = 'Choose the word that best describes your mood'
        self.fields['notes'].label = 'Additional Notes'
        self.fields['notes'].required = False
        self.fields['date'].label = 'Date'
    
    def clean_date(self):
        """Validate that the date is not in the future and not too far in the past"""
        date = self.cleaned_data.get('date')
        if date:
            today = timezone.now().date()
            if date > today:
                raise ValidationError("Mood entries cannot be created for future dates.")
            
            # Prevent entries more than 1 year in the past
            one_year_ago = today - timezone.timedelta(days=365)
            if date < one_year_ago:
                raise ValidationError("Mood entries cannot be created more than 1 year in the past.")
        return date
    
    def clean(self):
        """Validate that user doesn't have duplicate mood entries for the same date"""
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        
        if date and self.user:
            # Check for existing mood entry on the same date (excluding current instance)
            existing_entry = MoodEntry.objects.filter(
                user=self.user,
                date=date
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_entry.exists():
                raise ValidationError(
                    f"You already have a mood entry for {date.strftime('%B %d, %Y')}. "
                    "You can only log one mood per day."
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save the mood entry with the associated user"""
        mood_entry = super().save(commit=False)
        if self.user:
            mood_entry.user = self.user
        if commit:
            mood_entry.save()
        return mood_entry


class HabitForm(forms.ModelForm):
    """Form for creating and editing habits"""
    
    class Meta:
        model = Habit
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'e.g., Drink 8 glasses of water'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Optional description of your habit...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add custom labels and help text
        self.fields['name'].label = 'Habit Name'
        self.fields['name'].help_text = 'Give your habit a clear, specific name'
        self.fields['description'].label = 'Description'
        self.fields['description'].help_text = 'Optional details about this habit'
        self.fields['description'].required = False
        self.fields['is_active'].label = 'Active'
        self.fields['is_active'].help_text = 'Uncheck to pause tracking this habit'
        
        # Set default value for is_active
        if not self.instance.pk:
            self.fields['is_active'].initial = True
    
    def clean_name(self):
        """Validate habit name is unique for the user and meets requirements"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            
            # Check minimum length
            if len(name) < 2:
                raise ValidationError("Habit name must be at least 2 characters long.")
            
            # Check maximum length
            if len(name) > 100:
                raise ValidationError("Habit name cannot exceed 100 characters.")
            
            # Check for profanity or inappropriate content (basic check)
            inappropriate_words = ['test', 'dummy']  # Add more as needed
            if any(word in name.lower() for word in inappropriate_words):
                raise ValidationError("Please choose an appropriate habit name.")
            
            if self.user:
                # Check for existing habit with same name (excluding current instance)
                existing_habit = Habit.objects.filter(
                    user=self.user,
                    name__iexact=name
                ).exclude(pk=self.instance.pk if self.instance else None)
                
                if existing_habit.exists():
                    raise ValidationError(
                        f"You already have a habit named '{name}'. "
                        "Please choose a different name."
                    )
        
        return name
    
    def save(self, commit=True):
        """Save the habit with the associated user"""
        habit = super().save(commit=False)
        if self.user:
            habit.user = self.user
        if commit:
            habit.save()
        return habit


class HabitToggleForm(forms.Form):
    """Simple form for toggling habit completion status"""
    
    completed = forms.BooleanField(required=False)
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Optional notes...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['completed'].label = 'Completed'
        self.fields['notes'].label = 'Notes'