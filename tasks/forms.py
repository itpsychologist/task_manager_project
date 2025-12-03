from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Task, Worker, Project, Team, Tag, Comment


class WorkerRegistrationForm(UserCreationForm):
    """Worker registration form."""

    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(required=True, label="First Name")
    last_name = forms.CharField(required=True, label="Last Name")

    class Meta:
        model = Worker
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "position",
            "password1",
            "password2",
        ]


class TaskForm(forms.ModelForm):
    """Form for creating/editing a task."""

    class Meta:
        model = Task
        fields = [
            "name",
            "description",
            "task_type",
            "priority",
            "deadline",
            "assignees",
            "tags",
            "project",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "assignees": forms.CheckboxSelectMultiple(),
            "tags": forms.CheckboxSelectMultiple(),
        }


class ProjectForm(forms.ModelForm):
    """Form for creating/editing a project."""

    class Meta:
        model = Project
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class TeamForm(forms.ModelForm):
    """Form for creating/editing a team."""

    class Meta:
        model = Team
        fields = ["name", "members", "project"]
        widgets = {
            "members": forms.CheckboxSelectMultiple(),
        }


class TagForm(forms.ModelForm):
    """Form for creating/editing a tag."""

    class Meta:
        model = Tag
        fields = ["name"]


class CommentForm(forms.ModelForm):
    """Form for adding a comment."""

    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Add a comment...",
                    "class": "form-control",
                }
            ),
        }
        labels = {"content": "Comment"}
