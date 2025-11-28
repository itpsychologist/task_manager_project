from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Task, Worker, Project, Team, Tag, Comment


class WorkerRegistrationForm(UserCreationForm):
    """Форма реєстрації працівника"""
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=True, label="Ім'я")
    last_name = forms.CharField(required=True, label='Прізвище')

    class Meta:
        model = Worker
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'position', 'password1', 'password2'
        ]


class TaskForm(forms.ModelForm):
    """Форма для створення/редагування завдання"""

    class Meta:
        model = Task
        fields = [
            'name', 'description', 'task_type', 'priority',
            'deadline', 'assignees', 'tags', 'project'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'assignees': forms.CheckboxSelectMultiple(),
            'tags': forms.CheckboxSelectMultiple(),
        }


class ProjectForm(forms.ModelForm):
    """Форма для створення/редагування проєкту"""

    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class TeamForm(forms.ModelForm):
    """Форма для створення/редагування команди"""

    class Meta:
        model = Team
        fields = ['name', 'members', 'project']
        widgets = {
            'members': forms.CheckboxSelectMultiple(),
        }


class TagForm(forms.ModelForm):
    """Форма для створення/редагування мітки"""

    class Meta:
        model = Tag
        fields = ['name']


class CommentForm(forms.ModelForm):
    """Форма для додавання коментаря"""

    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Додайте коментар...',
                'class': 'form-control'
            }),
        }
        labels = {
            'content': 'Коментар'
        }
