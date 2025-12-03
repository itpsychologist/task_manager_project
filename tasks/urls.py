from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Автентифікація
    path("register/", views.RegisterView.as_view(), name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="tasks/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    path("dashboard/", views.dashboard, name="dashboard_alt"),
    # Завдання
    path("tasks/", views.TaskListView.as_view(), name="task_list"),
    path("my-tasks/", views.MyTasksView.as_view(), name="my_tasks"),
    path("tasks/create/", views.TaskCreateView.as_view(), name="task_create"),
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_edit"),
    path("tasks/<int:pk>/toggle/", views.task_toggle_status, name="task_toggle_status"),
    path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task_delete"),
    # Коментарі
    path("tasks/<int:pk>/comment/", views.task_add_comment, name="task_add_comment"),
    # Активність
    path("tasks/<int:pk>/activity/", views.task_activity, name="task_activity"),
    # Проєкти
    path("projects/", views.ProjectListView.as_view(), name="project_list"),
    path("projects/create/", views.ProjectCreateView.as_view(), name="project_create"),
    path(
        "projects/<int:pk>/", views.ProjectDetailView.as_view(), name="project_detail"
    ),
    path(
        "projects/<int:pk>/edit/",
        views.ProjectUpdateView.as_view(),
        name="project_edit",
    ),
    path(
        "projects/<int:pk>/delete/",
        views.ProjectDeleteView.as_view(),
        name="project_delete",
    ),
    path(
        "projects/<int:pk>/add-team/", views.project_add_team, name="project_add_team"
    ),
    path(
        "projects/<int:pk>/remove-team/<int:team_pk>/",
        views.project_remove_team,
        name="project_remove_team",
    ),
    # Команди
    path("teams/", views.TeamListView.as_view(), name="team_list"),
    path("teams/create/", views.TeamCreateView.as_view(), name="team_create"),
    path("teams/<int:pk>/", views.TeamDetailView.as_view(), name="team_detail"),
    path("teams/<int:pk>/edit/", views.TeamUpdateView.as_view(), name="team_edit"),
    path("teams/<int:pk>/delete/", views.TeamDeleteView.as_view(), name="team_delete"),
    path("teams/<int:pk>/add-member/", views.team_add_member, name="team_add_member"),
    path(
        "teams/<int:pk>/remove-member/<int:member_pk>/",
        views.team_remove_member,
        name="team_remove_member",
    ),
    # Мітки
    path("tags/", views.TagListView.as_view(), name="tag_list"),
    path("tags/create/", views.TagCreateView.as_view(), name="tag_create"),
    path("tags/<int:pk>/", views.TagDetailView.as_view(), name="tag_detail"),
    path("tags/<int:pk>/edit/", views.TagUpdateView.as_view(), name="tag_edit"),
    path("tags/<int:pk>/delete/", views.TagDeleteView.as_view(), name="tag_delete"),
    # Нотифікації
    path(
        "notifications/",
        views.NotificationListView.as_view(),
        name="notifications_list",
    ),
    path(
        "notifications/<int:pk>/read/",
        views.notification_mark_read,
        name="notification_mark_read",
    ),
    path(
        "notifications/read-all/",
        views.notification_mark_all_read,
        name="notification_mark_all_read",
    ),
    # Посади (тільки для superuser)
    path("positions/", views.PositionListView.as_view(), name="position_list"),
    path(
        "positions/create/", views.PositionCreateView.as_view(), name="position_create"
    ),
    path(
        "positions/<int:pk>/edit/",
        views.PositionUpdateView.as_view(),
        name="position_edit",
    ),
    path(
        "positions/<int:pk>/delete/",
        views.PositionDeleteView.as_view(),
        name="position_delete",
    ),
    # Працівники (тільки для superuser)
    path("workers/", views.WorkerListView.as_view(), name="worker_list"),
    path(
        "workers/<int:pk>/edit/", views.WorkerUpdateView.as_view(), name="worker_edit"
    ),
]
