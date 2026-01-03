from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from datetime import timedelta
from .models import (
    Task,
    Worker,
    Project,
    Tag,
    Team,
    ActivityLog,
    Notification,
    Position,
)
from .forms import (
    TaskForm,
    WorkerRegistrationForm,
    ProjectForm,
    TeamForm,
    TagForm,
    CommentForm,
)


# ==================== REGISTRATION ====================


class RegisterView(CreateView):
    """Register a new user."""

    model = Worker
    form_class = WorkerRegistrationForm
    template_name = "tasks/register.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Registration completed successfully!")
        return redirect(self.success_url)


# ==================== TASK VIEWS ====================


class TaskListView(LoginRequiredMixin, ListView):
    """List of all tasks."""

    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            Task.objects.all()
            .select_related("task_type", "project", "created_by")
            .prefetch_related("assignees", "tags")
        )

        # Filtering
        search = self.request.GET.get("search", "")
        status = self.request.GET.get("status", "")
        priority = self.request.GET.get("priority", "")
        project_id = self.request.GET.get("project", "")

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        if status == "completed":
            queryset = queryset.filter(is_completed=True)
        elif status == "incomplete":
            queryset = queryset.filter(is_completed=False)

        if priority:
            queryset = queryset.filter(priority=priority)

        if project_id:
            queryset = queryset.filter(project_id=project_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = Project.objects.all()
        context["search"] = self.request.GET.get("search", "")
        context["status"] = self.request.GET.get("status", "")
        context["priority"] = self.request.GET.get("priority", "")
        context["project_id"] = self.request.GET.get("project", "")
        context["today"] = timezone.now().date()
        return context


class MyTasksView(LoginRequiredMixin, ListView):
    """My tasks."""

    model = Task
    template_name = "tasks/my_task.html"
    context_object_name = "tasks"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        worker = self.request.user
        context["completed_tasks"] = worker.get_completed_tasks()
        context["incomplete_tasks"] = worker.get_incomplete_tasks()
        return context


class TaskCreateView(LoginRequiredMixin, CreateView):
    """Create a new task."""

    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Task created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("task_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Task"
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    """Detailed information about a task."""

    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a task."""

    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        return queryset

    def dispatch(self, request, *args, **kwargs):
        task = self.get_object()
        if task.created_by != request.user and not request.user.is_staff:
            messages.error(request,
                           "You do not have permission to edit this task")
            return redirect("task_detail", pk=task.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Task updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("task_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Task"
        context["task"] = self.object
        return context


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a task."""

    model = Task
    template_name = "tasks/task_confirm_delete.html"
    success_url = reverse_lazy("task_list")

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        return queryset

    def dispatch(self, request, *args, **kwargs):
        task = self.get_object()
        if task.created_by != request.user and not request.user.is_staff:
            messages.error(request,
                           "You do not have permission to edit this task")
            return redirect("task_detail", pk=task.pk)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Task deleted successfully!")
        return super().delete(request, *args, **kwargs)


@login_required
def task_toggle_status(request, pk):
    """Toggle task status (completed/incomplete)."""
    task = get_object_or_404(Task, pk=pk)

    if task.is_completed:
        task.mark_as_incomplete()
        messages.info(request, f'Task "{task.name}" marked as incomplete')
    else:
        task.mark_as_completed()
        messages.success(request, f'Task "{task.name}" marked as completed!')

    return redirect("task_detail", pk=task.pk)


# ==================== PROJECTS ====================


class ProjectListView(LoginRequiredMixin, ListView):
    """List of all projects."""

    model = Project
    template_name = "tasks/project_list.html"
    context_object_name = "projects"
    paginate_by = 10

    def get_queryset(self):
        queryset = Project.objects.all().prefetch_related("tasks", "teams")

        # Search filtering
        search = self.request.GET.get("search", "")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        return context


class ProjectDetailView(LoginRequiredMixin, DetailView):
    """Detailed information about a project."""

    model = Project
    template_name = "tasks/project_detail.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tasks"] = (
            self.object.tasks.all()
            .select_related("task_type", "created_by")
            .prefetch_related("assignees", "tags")
        )
        context["teams"] = self.object.teams.all().prefetch_related("members")
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """Create a new project."""

    model = Project
    form_class = ProjectForm
    template_name = "tasks/project_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Project created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("project_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Project"
        return context


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a project."""

    model = Project
    form_class = ProjectForm
    template_name = "tasks/project_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Project updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("project_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Project"
        context["project"] = self.object
        return context


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a project."""

    model = Project
    template_name = "tasks/project_confirm_delete.html"
    success_url = reverse_lazy("project_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Project deleted successfully!")
        return super().delete(request, *args, **kwargs)


# ==================== TEAMS ====================


class TeamListView(LoginRequiredMixin, ListView):
    """List of all teams."""

    model = Team
    template_name = "tasks/team_list.html"
    context_object_name = "teams"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            Team.objects.all()
            .select_related("project")
            .prefetch_related("members")
        )

        # Search filtering
        search = self.request.GET.get("search", "")
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        return context


class TeamDetailView(LoginRequiredMixin, DetailView):
    """Detailed information about a team."""

    model = Team
    template_name = "tasks/team_detail.html"
    context_object_name = "team"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["members"] = (
            self.object.members.all().select_related("position"))
        return context


class TeamCreateView(LoginRequiredMixin, CreateView):
    """Create a new team."""

    model = Team
    form_class = TeamForm
    template_name = "tasks/team_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Team created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("team_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Team"
        return context


class TeamUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a team."""

    model = Team
    form_class = TeamForm
    template_name = "tasks/team_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Team updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("team_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Team"
        context["team"] = self.object
        return context


class TeamDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a team."""

    model = Team
    template_name = "tasks/team_confirm_delete.html"
    success_url = reverse_lazy("team_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Team deleted successfully!")
        return super().delete(request, *args, **kwargs)


@login_required
def project_add_team(request, pk):
    """Add a team to a project."""
    project = get_object_or_404(Project, pk=pk)

    if request.method == "POST":
        team_id = request.POST.get("team_id")
        if team_id:
            team = get_object_or_404(Team, pk=team_id)
            team.project = project
            team.save()
            messages.success(
                request, f'Team "{team.name}" successfully added to project!'
            )
        return redirect("project_detail", pk=project.pk)

    # Get teams that are not assigned to any project or to this project
    available_teams = (
        Team.objects.filter(Q(project__isnull=True) | Q(project=project))
    )

    context = {
        "project": project,
        "available_teams": available_teams,
    }
    return render(request, "tasks/project_add_team.html", context)


@login_required
def project_remove_team(request, pk, team_pk):
    """Remove a team from a project."""
    project = get_object_or_404(Project, pk=pk)
    team = get_object_or_404(Team, pk=team_pk, project=project)

    if request.method == "POST":
        team.project = None
        team.save()
        messages.success(request, f'Team "{team.name}" removed from project!')
        return redirect("project_detail", pk=project.pk)

    context = {
        "project": project,
        "team": team,
    }
    return render(request, "tasks/project_remove_team.html", context)


@login_required
def team_add_member(request, pk):
    """Add a member to a team."""
    team = get_object_or_404(Team, pk=pk)

    if request.method == "POST":
        member_id = request.POST.get("member_id")
        if member_id:
            member = get_object_or_404(Worker, pk=member_id)
            team.members.add(member)
            messages.success(request,
                             f'User "{member.get_full_name()}" added to team!')
        return redirect("team_detail", pk=team.pk)

    # Get workers not in this team
    current_members = team.members.all()
    available_workers = Worker.objects.exclude(id__in=current_members)

    context = {
        "team": team,
        "available_workers": available_workers,
    }
    return render(request, "tasks/team_add_member.html", context)


@login_required
def team_remove_member(request, pk, member_pk):
    """Remove a member from a team."""
    team = get_object_or_404(Team, pk=pk)
    member = get_object_or_404(Worker, pk=member_pk)

    if request.method == "POST":
        team.members.remove(member)
        messages.success(request,
                         f'User "{member.get_full_name()}" removed from team!')
        return redirect("team_detail", pk=team.pk)

    context = {
        "team": team,
        "member": member,
    }
    return render(request, "tasks/team_remove_member.html", context)


# ==================== TAGS ====================


class TagListView(LoginRequiredMixin, ListView):
    """List of all tags."""

    model = Tag
    template_name = "tasks/tag_list.html"
    context_object_name = "tags"
    paginate_by = 10

    def get_queryset(self):
        queryset = Tag.objects.all().prefetch_related("tasks")

        # Search filtering
        search = self.request.GET.get("search", "")
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        return context


class TagDetailView(LoginRequiredMixin, DetailView):
    """Detailed information about a tag."""

    model = Tag
    template_name = "tasks/tag_detail.html"
    context_object_name = "tag"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tasks"] = (
            self.object.tasks.all()
            .select_related("task_type", "project", "created_by")
            .prefetch_related("assignees")
        )
        return context


class TagCreateView(LoginRequiredMixin, CreateView):
    """Create a new tag."""

    model = Tag
    form_class = TagForm
    template_name = "tasks/tag_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Tag created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("tag_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Tag"
        return context


class TagUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a tag."""

    model = Tag
    form_class = TagForm
    template_name = "tasks/tag_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Tag updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("tag_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Tag"
        context["tag"] = self.object
        return context


class TagDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a tag."""

    model = Tag
    template_name = "tasks/tag_confirm_delete.html"
    success_url = reverse_lazy("tag_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Tag deleted successfully!")
        return super().delete(request, *args, **kwargs)


# ==================== DASHBOARD ====================


@login_required
def dashboard(request):
    """Dashboard with statistics."""
    user = request.user

    # General statistics
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(is_completed=True).count()
    incomplete_tasks = Task.objects.filter(is_completed=False).count()

    # Tasks with approaching deadline (next 7 days)
    upcoming_deadline = timezone.now().date() + timedelta(days=7)
    upcoming_tasks = Task.objects.filter(
        is_completed=False,
        deadline__lte=upcoming_deadline,
        deadline__gte=timezone.now().date(),
    ).order_by("deadline")[:5]

    # Overdue tasks
    overdue_tasks = Task.objects.filter(
        is_completed=False, deadline__lt=timezone.now().date()
    ).count()

    # My tasks
    my_tasks = user.assigned_tasks.filter(is_completed=False).count()
    my_completed = user.assigned_tasks.filter(is_completed=True).count()

    # Priority statistics
    priority_stats_raw = (
        Task.objects.filter(is_completed=False)
        .values("priority")
        .annotate(count=Count("id"))
    )

    # Convert to JSON-serializable format
    import json

    priority_stats = json.dumps(list(priority_stats_raw))

    # Recent activity
    recent_activity = (
        ActivityLog.objects.all()
        .select_related("task", "user")
        .order_by("-created_at")[:10]
    )

    # Projects
    projects = Project.objects.all().prefetch_related("tasks")[:5]

    context = {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "incomplete_tasks": incomplete_tasks,
        "overdue_tasks": overdue_tasks,
        "my_tasks": my_tasks,
        "my_completed": my_completed,
        "upcoming_tasks": upcoming_tasks,
        "priority_stats": priority_stats,
        "recent_activity": recent_activity,
        "projects": projects,
    }

    return render(request, "tasks/dashboard.html", context)


# ==================== COMMENTS ====================


@login_required
def task_add_comment(request, pk):
    """Add a comment to a task."""
    task = get_object_or_404(Task, pk=pk)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "comment": {
                            "author": comment.author.get_full_name(),
                            "content": comment.content,
                            "created_at":
                                comment.created_at.strftime("%d.%m.%Y %H:%M"),
                        },
                    }
                )

            messages.success(request, "Comment added!")
            return redirect("task_detail", pk=task.pk)

    return redirect("task_detail", pk=task.pk)


# ==================== NOTIFICATIONS ====================


class NotificationListView(LoginRequiredMixin, ListView):
    """List of user notifications."""

    model = Notification
    template_name = "tasks/notifications.html"
    context_object_name = "notifications"
    paginate_by = 15

    def get_queryset(self):
        queryset = (
            self.request.user.notifications.all()
            .select_related("task")
            .order_by("-created_at")
        )

        # Filtering
        filter_type = self.request.GET.get("filter", "all")
        if filter_type == "unread":
            queryset = queryset.filter(is_read=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_type"] = self.request.GET.get("filter", "all")
        return context


# ==================== ACTIVITY LOG ====================


@login_required
def task_activity(request, pk):
    """Get task activity (for AJAX)."""
    task = get_object_or_404(Task, pk=pk)
    activities = task.get_activity_log()

    activity_list = [
        {
            "user": activity.user.get_full_name()
            if activity.user else "System",
            "type": activity.get_activity_type_display(),
            "description": activity.description,
            "created_at": activity.created_at.strftime("%d.%m.%Y %H:%M"),
        }
        for activity in activities
    ]

    return JsonResponse({"activities": activity_list})


# ==================== POSITIONS (SUPERUSER ONLY) ====================


class PositionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List of positions (superuser only)."""

    model = Position
    template_name = "tasks/position_list.html"
    context_object_name = "positions"

    def test_func(self):
        return self.request.user.is_superuser


class PositionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new position (superuser only)."""

    model = Position
    template_name = "tasks/position_form.html"
    fields = ["name"]
    success_url = reverse_lazy("position_list")

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Position "{form.instance.name}" created successfully!'
        )
        return super().form_valid(form)


class PositionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit a position (superuser only)."""

    model = Position
    template_name = "tasks/position_form.html"
    fields = ["name"]
    success_url = reverse_lazy("position_list")

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Position "{form.instance.name}" updated successfully!'
        )
        return super().form_valid(form)


class PositionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a position (superuser only)."""

    model = Position
    template_name = "tasks/position_confirm_delete.html"
    success_url = reverse_lazy("position_list")

    def test_func(self):
        return self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        position = self.get_object()
        messages.success(request,
                         f'Position "{position.name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def notification_mark_read(request, pk):
    """Mark notification as read."""
    notification = get_object_or_404(Notification,
                                     pk=pk,
                                     recipient=request.user)
    notification.mark_as_read()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True})

    return redirect("notifications_list")


@login_required
def notification_mark_all_read(request):
    """Mark all notifications as read."""
    request.user.notifications.filter(is_read=False).update(is_read=True)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True})

    messages.success(request, "All notifications marked as read")
    return redirect("notifications_list")


# ==================== WORKERS MANAGEMENT (SUPERUSER ONLY) ====================


class WorkerListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List of workers (superuser only)."""

    model = Worker
    template_name = "tasks/worker_list.html"
    context_object_name = "workers"
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        queryset = (
            Worker.objects.all()
            .select_related("position")
            .order_by("-date_joined")
        )

        # Search filtering
        search = self.request.GET.get("search", "")
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        return context


class WorkerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit a worker (superuser only)."""

    model = Worker
    template_name = "tasks/worker_edit.html"
    fields = ["first_name", "last_name", "email", "position"]
    success_url = reverse_lazy("worker_list")

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Worker "{form.instance.get_full_name()}" data updated!'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["worker"] = self.object
        return context
