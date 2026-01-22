from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Comment, Project, Task, Team


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'team']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'team': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['team'].queryset = Team.objects.filter(members=user)

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'status', 'due_date', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['assigned_to'].queryset = project.team.members.all()


class AddMemberForm(forms.Form):
    username = forms.CharField(
        label="Login użytkownika", 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def __init__(self, team, *args, **kwargs):
        """
        Przyjmujemy obiekt 'team' jako argument, aby móc sprawdzić
        członkostwo w metodzie clean().
        """
        self.team = team
        super().__init__(*args, **kwargs)
        self.user_to_add = None

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')

        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise ValidationError(f"Użytkownik o loginie '{username}' nie istnieje.")

            if self.team.members.filter(pk=user.pk).exists():
                raise ValidationError("Ten użytkownik już należy do tego zespołu.")

            self.user_to_add = user

        return cleaned_data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        labels = {
            'content': ''
        }
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Napisz komentarz...'
            }),
        }
