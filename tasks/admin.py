from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Worker,
    Position,
    TaskType,
    Task,
    Tag,
    Project,
    Team,
    Comment,
    ActivityLog,
    Notification,
)


class WorkerAdmin(UserAdmin):
    """Worker administration."""

    model = Worker
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "position",
        "is_staff",
    ]
    list_filter = ["position", "is_staff", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["username"]

    fieldsets = UserAdmin.fieldsets + (
        ("Additional Information", {"fields": ("position",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Additional Information",
            {"fields": ("position", "email", "first_name", "last_name")},
        ),
    )


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Position administration."""

    list_display = ["name"]
    search_fields = ["name"]


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    """Task type administration."""

    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Task administration."""

    list_display = [
        "name",
        "task_type",
        "priority",
        "deadline",
        "is_completed",
        "created_by",
        "created_at",
    ]
    list_filter = ["is_completed", "priority", "task_type", "created_at"]
    search_fields = ["name", "description"]
    date_hierarchy = "created_at"
    filter_horizontal = ["assignees", "tags"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name",
                        "description",
                        "task_type",
                        "priority",
                        "deadline")},
        ),
        ("Assignment", {"fields": ("assignees",
                                   "tags",
                                   "project",
                                   "created_by")}),
        ("Status", {"fields": ("is_completed",)}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Tag administration."""

    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Project administration."""

    list_display = ["name", "created_at"]
    search_fields = ["name", "description"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at"]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Team administration."""

    list_display = ["name", "project"]
    list_filter = ["project"]
    search_fields = ["name"]
    filter_horizontal = ["members"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Comment administration."""

    list_display = ["task", "author", "created_at", "content_preview"]
    list_filter = ["created_at"]
    search_fields = ["content", "task__name", "author__username"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at", "updated_at"]

    def content_preview(self, obj):
        """Show first 50 characters of the comment."""
        if len(obj.content) > 50:
            return obj.content[:50] + "..."
        return obj.content

    content_preview.short_description = "Content"


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Activity log administration."""

    list_display = [
        "task",
        "user",
        "activity_type",
        "created_at",
        "description_preview",
    ]
    list_filter = ["activity_type", "created_at"]
    search_fields = ["description", "task__name", "user__username"]
    date_hierarchy = "created_at"
    readonly_fields = ["task",
                       "user",
                       "activity_type",
                       "description",
                       "created_at"]

    def description_preview(self, obj):
        """Show first 50 characters of the description."""
        if len(obj.description) > 50:
            return obj.description[:50] + "..."
        return obj.description

    description_preview.short_description = "Description"

    def has_add_permission(self, request):
        """Prohibit manual addition of records."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prohibit deletion of records."""
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification administration."""

    list_display = ["recipient",
                    "notification_type",
                    "title", "is_read",
                    "created_at"]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["title", "message", "recipient__username"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at"]

    actions = ["mark_as_read", "mark_as_unread"]

    def mark_as_read(self, request, queryset):
        """Mark as read."""
        queryset.update(is_read=True)

    mark_as_read.short_description = "Mark as read"

    def mark_as_unread(self, request, queryset):
        """Mark as unread."""
        queryset.update(is_read=False)

    mark_as_unread.short_description = "Mark as unread"


admin.site.register(Worker, WorkerAdmin)
