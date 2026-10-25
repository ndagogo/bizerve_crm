from django import forms
from .models import Task, TaskDocument, TaskComment
from django.contrib.auth import get_user_model

class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'task_type', 'description', 'assigned_to', 'expected_completion', 'priority', 'amount']
        widgets = {
            'expected_completion': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Only show staff users in assigned_to field
        if self.request and self.request.user.is_authenticated:
            User = get_user_model()
            staff_users = User.objects.filter(user_type='staff')
            self.fields['assigned_to'].queryset = staff_users

class TaskUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'task_type', 'description', 'priority', 'amount']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class TaskQueryForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Explain why this task needs modification...',
            'class': 'form-control',
        }),
        label='Query Reason'
    )

class TaskDocumentForm(forms.ModelForm):
    class Meta:
        model = TaskDocument
        fields = ['file', 'document_type', 'description', 'is_final']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'document_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Document type'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'is_final': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Add a comment...',
                'class': 'form-control'
            }),
        }

class TaskDeclineForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Explain why you cannot accept this task...'}),
        label='Decline Reason',
        required=True
    )