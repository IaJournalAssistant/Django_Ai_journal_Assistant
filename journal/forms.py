from django import forms
from .models import JournalEntry, Note, Tag
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

class NoteForm(forms.ModelForm):
    # Let user choose from existing tags. No inline creation here.
    tags = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        empty_label="-- choose a tag --",
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg py-3 px-4 bg-gray-100'
        })
    )

    class Meta:
        model = Note
        fields = ['title', 'content', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full rounded-lg py-3 px-4 bg-gray-100', 'placeholder': 'Title'}),
            'content': forms.Textarea(attrs={'rows': 6, 'class': 'w-full rounded-lg py-3 px-4 bg-gray-100'}),
        }


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Tag name'})
        }
# We'll handle multiple files in the template/view directly
# This form is just for reference, actual file handling is done in views