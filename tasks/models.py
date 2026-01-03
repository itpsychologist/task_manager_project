from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_deadline(value):
    """Validate that deadline is not in the past."""
    if value < timezone.now().date():
        raise ValidationError("Deadline cannot be in the past")


class Position(models.Model):
    """Employee position."""

    name = models.CharField(max_length=100,
                            unique=True,
                            verbose_name="Position Name")

    class Meta:
        verbose_name = "Position"
        verbose_name_plural = "Positions"

    def __str__(self):
        return self.name


class Worker(AbstractUser):
    """Worker (extended user model)."""

    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        related_name="workers",
        verbose_name="Position",
    )
    email = models.EmailField(
        unique=True, validators=[EmailValidator()], verbose_name="Email"
    )
    first_name = models.CharField(max_length=150, verbose_name="First Name")
    last_name = models.CharField(max_length=150, verbose_name="Last Name")

    class Meta:
        verbose_name = "Worker"
        verbose_name_plural = "Workers"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.position})"

    def get_completed_tasks(self):
        """Return completed tasks for the worker."""
        return self.assigned_tasks.filter(is_completed=True)

    def get_incomplete_tasks(self):
        """Return incomplete tasks for the worker."""
        return self.assigned_tasks.filter(is_completed=False)

    def get_unread_notifications_count(self):
        """Return count of unread notifications."""
        return self.notifications.filter(is_read=False).count()

    def get_unread_notifications(self):
        """Return unread notifications."""
        return self.notifications.filter(is_read=False).order_by("-created_at")


class TaskType(models.Model):
    """Task type."""

    name = models.CharField(max_length=100,
                            unique=True,
                            verbose_name="Type Name")

    class Meta:
        verbose_name = "Task Type"
        verbose_name_plural = "Task Types"

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag for tasks."""

    name = models.CharField(max_length=100,
                            unique=True,
                            verbose_name="Tag Name")

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name


class Project(models.Model):
    """Project."""

    name = models.CharField(max_length=200, verbose_name="Project Name")
    description = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name="Created At")

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.name


class Team(models.Model):
    """Team."""

    name = models.CharField(max_length=200, verbose_name="Team Name")
    members = models.ManyToManyField(
        Worker, related_name="teams", verbose_name="Team Members"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="teams",
        null=True,
        blank=True,
        verbose_name="Project",
    )

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self):
        return self.name


class Task(models.Model):
    """Task."""

    PRIORITY_CHOICES = [
        ("Urgent", "Urgent"),
        ("High", "High"),
        ("Medium", "Medium"),
        ("Low", "Low"),
    ]

    name = models.CharField(max_length=200, verbose_name="Task Name")
    description = models.TextField(verbose_name="Description")
    deadline = models.DateField(verbose_name="Deadline",
                                validators=[validate_deadline])
    is_completed = models.BooleanField(default=False, verbose_name="Completed")
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="Medium",
        verbose_name="Priority",
    )
    task_type = models.ForeignKey(
        TaskType,
        on_delete=models.SET_NULL,
        null=True,
        related_name="tasks",
        verbose_name="Task Type",
    )
    assignees = models.ManyToManyField(
        Worker, related_name="assigned_tasks", verbose_name="Assignees"
    )
    tags = models.ManyToManyField(
        Tag, related_name="tasks", blank=True, verbose_name="Tags"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
        verbose_name="Project",
    )
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tasks",
        verbose_name="Created By",
    )
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True,
                                      verbose_name="Updated At")

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_priority_display()})"

    def mark_as_completed(self):
        """Mark task as completed."""
        self.is_completed = True
        self.save()

    def mark_as_incomplete(self):
        """Mark task as incomplete."""
        self.is_completed = False
        self.save()

    def get_activity_log(self):
        """Return all activity for the task."""
        return self.activity_logs.all().order_by("-created_at")

    def get_comments(self):
        """Return all comments for the task."""
        return self.comments.all().order_by("-created_at")

    def get_completion_percentage(self):
        """Return completion percentage (0 or 100)."""
        return 100 if self.is_completed else 0


class Comment(models.Model):
    """Comment on a task."""

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Task"
    )
    author = models.ForeignKey(
        Worker, on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Author"
    )
    content = models.TextField(verbose_name="Comment Content")
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True,
                                      verbose_name="Updated At")

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.task.name}"


class ActivityLog(models.Model):
    """Activity log for tracking changes."""

    ACTIVITY_TYPES = [
        ("created", "Created"),
        ("updated", "Updated"),
        ("completed", "Completed"),
        ("reopened", "Reopened"),
        ("assigned", "Assigned"),
        ("unassigned", "Unassigned"),
        ("commented", "Commented"),
        ("deleted", "Deleted"),
    ]

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="activity_logs",
        null=True,
        blank=True,
        verbose_name="Task",
    )
    user = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name="activities",
        verbose_name="User",
    )
    activity_type = models.CharField(
        max_length=20, choices=ACTIVITY_TYPES, verbose_name="Activity Type"
    )
    description = models.TextField(verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name="Created At")

    class Meta:
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.description}"


class Notification(models.Model):
    """Notification for a user."""

    NOTIFICATION_TYPES = [
        ("task_assigned", "Task Assigned"),
        ("task_completed", "Task Completed"),
        ("task_commented", "New Comment"),
        ("deadline_approaching", "Deadline Approaching"),
        ("task_updated", "Task Updated"),
    ]

    recipient = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Recipient",
    )
    notification_type = models.CharField(
        max_length=30, choices=NOTIFICATION_TYPES,
        verbose_name="Notification Type"
    )
    title = models.CharField(max_length=200, verbose_name="Title")
    message = models.TextField(verbose_name="Message")
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
        verbose_name="Task",
    )
    is_read = models.BooleanField(default=False,
                                  verbose_name="Read")
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name="Created At")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} for {self.recipient}"

    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.save()
