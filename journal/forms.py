from django import forms
from .models import JournalEntry
from media_manager.models import MediaFile

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter journal title...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 8,
                'placeholder': 'Write your journal entry...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make title optional since we extract it from content
        self.fields['title'].required = False

class UnifiedNoteForm(forms.ModelForm):
    """Form for the new unified note editor"""
    class Meta:
        model = JournalEntry
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full h-full resize-none border-0 focus:ring-0 text-gray-900 placeholder-gray-400 text-lg leading-relaxed',
                'placeholder': '# Untitled Note\n\nStart writing your note here...',
                'style': 'font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; outline: none;'
            }),
        }