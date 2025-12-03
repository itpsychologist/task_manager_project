from datetime import timedelta
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from tasks.models import (
    Position,
    Worker,
    Task,
    TaskType,
    Tag,
    Project,
    Team,
    Comment,
    ActivityLog,
    Notification,
    validate_deadline,
)
from tasks.forms import (
    WorkerRegistrationForm,
    TaskForm,
    ProjectForm,
    TeamForm,
    TagForm,
    CommentForm,
)


class PositionModelTest(TestCase):
    """Test Position model."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")

    def test_position_creation(self):
        """Test position is created correctly."""
        self.assertEqual(self.position.name, "Developer")
        self.assertIsNotNone(self.position.id)

    def test_position_str(self):
        """Test position string representation."""
        self.assertEqual(str(self.position), "Developer")

    def test_position_unique_name(self):
        """Test position name must be unique."""
        with self.assertRaises(Exception):
            Position.objects.create(name="Developer")


class WorkerModelTest(TestCase):
    """Test Worker model."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.worker = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")

    def test_worker_creation(self):
        """Test worker is created correctly."""
        self.assertEqual(self.worker.username, "testuser")
        self.assertEqual(self.worker.email, "test@example.com")
        self.assertEqual(self.worker.first_name, "John")
        self.assertEqual(self.worker.last_name, "Doe")
        self.assertEqual(self.worker.position, self.position)

    def test_worker_str(self):
        """Test worker string representation."""
        expected = f"{self.worker.first_name} {self.worker.last_name} ({self.position})"
        self.assertEqual(str(self.worker), expected)

    def test_get_completed_tasks(self):
        """Test get_completed_tasks method."""
        # Create completed task
        completed_task = Task.objects.create(
            name="Completed Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            is_completed=True,
            task_type=self.task_type,
            created_by=self.worker,
        )
        completed_task.assignees.add(self.worker)

        # Create incomplete task
        incomplete_task = Task.objects.create(
            name="Incomplete Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            is_completed=False,
            task_type=self.task_type,
            created_by=self.worker,
        )
        incomplete_task.assignees.add(self.worker)

        completed = self.worker.get_completed_tasks()
        self.assertEqual(completed.count(), 1)
        self.assertEqual(completed.first(), completed_task)

    def test_get_incomplete_tasks(self):
        """Test get_incomplete_tasks method."""
        # Create tasks
        completed_task = Task.objects.create(
            name="Completed Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            is_completed=True,
            task_type=self.task_type,
            created_by=self.worker,
        )
        completed_task.assignees.add(self.worker)

        incomplete_task = Task.objects.create(
            name="Incomplete Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            is_completed=False,
            task_type=self.task_type,
            created_by=self.worker,
        )
        incomplete_task.assignees.add(self.worker)

        incomplete = self.worker.get_incomplete_tasks()
        self.assertEqual(incomplete.count(), 1)
        self.assertEqual(incomplete.first(), incomplete_task)

    def test_get_unread_notifications_count(self):
        """Test get_unread_notifications_count method."""
        task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.worker,
        )

        # Create unread notifications
        Notification.objects.create(
            recipient=self.worker,
            notification_type="task_assigned",
            title="Test Notification 1",
            message="Test message",
            task=task,
            is_read=False,
        )
        Notification.objects.create(
            recipient=self.worker,
            notification_type="task_assigned",
            title="Test Notification 2",
            message="Test message",
            task=task,
            is_read=False,
        )

        # Create read notification
        Notification.objects.create(
            recipient=self.worker,
            notification_type="task_assigned",
            title="Test Notification 3",
            message="Test message",
            task=task,
            is_read=True,
        )

        self.assertEqual(self.worker.get_unread_notifications_count(), 2)

    def test_get_unread_notifications(self):
        """Test get_unread_notifications method."""
        task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.worker,
        )

        # Create notifications
        unread1 = Notification.objects.create(
            recipient=self.worker,
            notification_type="task_assigned",
            title="Unread 1",
            message="Test",
            task=task,
            is_read=False,
        )
        unread2 = Notification.objects.create(
            recipient=self.worker,
            notification_type="task_assigned",
            title="Unread 2",
            message="Test",
            task=task,
            is_read=False,
        )
        Notification.objects.create(
            recipient=self.worker,
            notification_type="task_assigned",
            title="Read",
            message="Test",
            task=task,
            is_read=True,
        )

        unread = self.worker.get_unread_notifications()
        self.assertEqual(unread.count(), 2)
        # Should be ordered by -created_at (most recent first)
        # Since unread2 was created last, it should be first
        self.assertIn(unread.first().title, ["Unread 1", "Unread 2"])


class TaskModelTest(TestCase):
    """Test Task model."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.worker = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.project = Project.objects.create(
            name="Test Project", description="Test description"
        )

    def test_task_creation(self):
        """Test task is created correctly."""
        task = Task.objects.create(
            name="Test Task",
            description="Test description",
            deadline=timezone.now().date() + timedelta(days=1),
            priority="High",
            task_type=self.task_type,
            project=self.project,
            created_by=self.worker,
        )
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.priority, "High")
        self.assertFalse(task.is_completed)

    def test_task_str(self):
        """Test task string representation."""
        task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            priority="High",
            task_type=self.task_type,
            created_by=self.worker,
        )
        self.assertEqual(str(task), "Test Task (High)")

    def test_validate_deadline_future(self):
        """Test deadline validation accepts future dates."""
        future_date = timezone.now().date() + timedelta(days=1)
        try:
            validate_deadline(future_date)
        except ValidationError:
            self.fail("validate_deadline raised ValidationError for future date")

    def test_validate_deadline_past(self):
        """Test deadline validation rejects past dates."""
        past_date = timezone.now().date() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            validate_deadline(past_date)

    def test_mark_as_completed(self):
        """Test mark_as_completed method."""
        task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.worker,
        )
        self.assertFalse(task.is_completed)
        task.mark_as_completed()
        self.assertTrue(task.is_completed)

    def test_mark_as_incomplete(self):
        """Test mark_as_incomplete method."""
        task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            is_completed=True,
            task_type=self.task_type,
            created_by=self.worker,
        )
        self.assertTrue(task.is_completed)
        task.mark_as_incomplete()
        self.assertFalse(task.is_completed)

    def test_get_completion_percentage(self):
        """Test get_completion_percentage method."""
        task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.worker,
        )
        self.assertEqual(task.get_completion_percentage(), 0)

        task.mark_as_completed()
        self.assertEqual(task.get_completion_percentage(), 100)

    def test_get_activity_log(self):
        """Test get_activity_log method."""
        task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.worker,
        )

        # Signal already created one log, so we add one more
        ActivityLog.objects.create(
            task=task,
            user=self.worker,
            activity_type="updated",
            description="Task updated",
        )

        logs = task.get_activity_log()
        # Should have at least 2 logs (one from signal, one we created)
        self.assertGreaterEqual(logs.count(), 2)

    def test_get_comments(self):
        """Test get_comments method."""
        task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.worker,
        )

        Comment.objects.create(task=task, author=self.worker, content="First comment")
        Comment.objects.create(task=task, author=self.worker, content="Second comment")

        comments = task.get_comments()
        self.assertEqual(comments.count(), 2)


class CommentModelTest(TestCase):
    """Test Comment model."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.worker = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.worker,
        )

    def test_comment_creation(self):
        """Test comment is created correctly."""
        comment = Comment.objects.create(
            task=self.task, author=self.worker, content="Test comment"
        )
        self.assertEqual(comment.content, "Test comment")
        self.assertEqual(comment.task, self.task)
        self.assertEqual(comment.author, self.worker)

    def test_comment_str(self):
        """Test comment string representation."""
        comment = Comment.objects.create(
            task=self.task, author=self.worker, content="Test comment"
        )
        expected = f"Comment by {self.worker} on {self.task.name}"
        self.assertEqual(str(comment), expected)


class ActivityLogModelTest(TestCase):
    """Test ActivityLog model."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.worker = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.worker,
        )

    def test_activity_log_creation(self):
        """Test activity log is created correctly."""
        log = ActivityLog.objects.create(
            task=self.task,
            user=self.worker,
            activity_type="created",
            description="Task created",
        )
        self.assertEqual(log.task, self.task)
        self.assertEqual(log.user, self.worker)
        self.assertEqual(log.activity_type, "created")

    def test_activity_log_str(self):
        """Test activity log string representation."""
        log = ActivityLog.objects.create(
            task=self.task,
            user=self.worker,
            activity_type="created",
            description="Task created",
        )
        self.assertEqual(str(log), "Created - Task created")

    def test_activity_types(self):
        """Test all activity types are valid."""
        valid_types = [
            "created",
            "updated",
            "completed",
            "reopened",
            "assigned",
            "unassigned",
            "commented",
            "deleted",
        ]
        for activity_type in valid_types:
            log = ActivityLog.objects.create(
                task=self.task,
                user=self.worker,
                activity_type=activity_type,
                description=f"Test {activity_type}",
            )
            self.assertEqual(log.activity_type, activity_type)


class NotificationModelTest(TestCase):
    """Test Notification model."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.worker = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.worker,
        )

    def test_notification_creation(self):
        """Test notification is created correctly."""
        notification = Notification.objects.create(
            recipient=self.worker,
            notification_type="task_assigned",
            title="New Task",
            message="You have been assigned a task",
            task=self.task,
        )
        self.assertEqual(notification.recipient, self.worker)
        self.assertFalse(notification.is_read)

    def test_notification_str(self):
        """Test notification string representation."""
        notification = Notification.objects.create(
            recipient=self.worker,
            notification_type="task_assigned",
            title="New Task",
            message="Test message",
            task=self.task,
        )
        expected = f"New Task for {self.worker}"
        self.assertEqual(str(notification), expected)

    def test_mark_as_read(self):
        """Test mark_as_read method."""
        notification = Notification.objects.create(
            recipient=self.worker,
            notification_type="task_assigned",
            title="New Task",
            message="Test message",
            task=self.task,
        )
        self.assertFalse(notification.is_read)
        notification.mark_as_read()
        self.assertTrue(notification.is_read)

    def test_notification_types(self):
        """Test all notification types are valid."""
        valid_types = [
            "task_assigned",
            "task_completed",
            "task_commented",
            "deadline_approaching",
            "task_updated",
        ]
        for notif_type in valid_types:
            notification = Notification.objects.create(
                recipient=self.worker,
                notification_type=notif_type,
                title="Test",
                message="Test message",
                task=self.task,
            )
            self.assertEqual(notification.notification_type, notif_type)


class ProjectModelTest(TestCase):
    """Test Project model."""

    def test_project_creation(self):
        """Test project is created correctly."""
        project = Project.objects.create(
            name="Test Project", description="Test description"
        )
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.description, "Test description")

    def test_project_str(self):
        """Test project string representation."""
        project = Project.objects.create(name="Test Project")
        self.assertEqual(str(project), "Test Project")


class TeamModelTest(TestCase):
    """Test Team model."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.worker1 = Worker.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.worker2 = Worker.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="pass123",
            first_name="Jane",
            last_name="Smith",
            position=self.position,
        )
        self.project = Project.objects.create(name="Test Project")

    def test_team_creation(self):
        """Test team is created correctly."""
        team = Team.objects.create(name="Test Team", project=self.project)
        team.members.add(self.worker1, self.worker2)
        self.assertEqual(team.name, "Test Team")
        self.assertEqual(team.members.count(), 2)

    def test_team_str(self):
        """Test team string representation."""
        team = Team.objects.create(name="Test Team")
        self.assertEqual(str(team), "Test Team")


class TagModelTest(TestCase):
    """Test Tag model."""

    def test_tag_creation(self):
        """Test tag is created correctly."""
        tag = Tag.objects.create(name="urgent")
        self.assertEqual(tag.name, "urgent")

    def test_tag_str(self):
        """Test tag string representation."""
        tag = Tag.objects.create(name="urgent")
        self.assertEqual(str(tag), "urgent")

    def test_tag_unique_name(self):
        """Test tag name must be unique."""
        Tag.objects.create(name="urgent")
        with self.assertRaises(Exception):
            Tag.objects.create(name="urgent")


class TaskTypeModelTest(TestCase):
    """Test TaskType model."""

    def test_task_type_creation(self):
        """Test task type is created correctly."""
        task_type = TaskType.objects.create(name="Bug Fix")
        self.assertEqual(task_type.name, "Bug Fix")

    def test_task_type_str(self):
        """Test task type string representation."""
        task_type = TaskType.objects.create(name="Bug Fix")
        self.assertEqual(str(task_type), "Bug Fix")

    def test_task_type_unique_name(self):
        """Test task type name must be unique."""
        TaskType.objects.create(name="Bug Fix")
        with self.assertRaises(Exception):
            TaskType.objects.create(name="Bug Fix")
class WorkerRegistrationFormTest(TestCase):
    """Test WorkerRegistrationForm."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")

    def test_valid_form(self):
        """Test form with valid data."""
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "position": self.position.id,
            "password1": "testpass123!@#",
            "password2": "testpass123!@#",
        }
        form = WorkerRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_required_fields(self):
        """Test form with missing required fields."""
        form_data = {
            "username": "testuser",
            "password1": "testpass123!@#",
            "password2": "testpass123!@#",
        }
        form = WorkerRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("first_name", form.errors)
        self.assertIn("last_name", form.errors)

    def test_invalid_email(self):
        """Test form with invalid email."""
        form_data = {
            "username": "testuser",
            "email": "invalid-email",
            "first_name": "John",
            "last_name": "Doe",
            "position": self.position.id,
            "password1": "testpass123!@#",
            "password2": "testpass123!@#",
        }
        form = WorkerRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_password_mismatch(self):
        """Test form with mismatched passwords."""
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "position": self.position.id,
            "password1": "testpass123!@#",
            "password2": "differentpass123!@#",
        }
        form = WorkerRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_duplicate_username(self):
        """Test form with duplicate username."""
        Worker.objects.create_user(
            username="testuser",
            email="existing@example.com",
            password="pass123",
            first_name="Existing",
            last_name="User",
        )
        form_data = {
            "username": "testuser",
            "email": "new@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "position": self.position.id,
            "password1": "testpass123!@#",
            "password2": "testpass123!@#",
        }
        form = WorkerRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)


class TaskFormTest(TestCase):
    """Test TaskForm."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.worker = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.project = Project.objects.create(name="Test Project")
        self.tag = Tag.objects.create(name="urgent")

    def test_valid_form(self):
        """Test form with valid data."""
        form_data = {
            "name": "Test Task",
            "description": "Test description",
            "task_type": self.task_type.id,
            "priority": "High",
            "deadline": (timezone.now().date() + timedelta(days=1)).isoformat(),
            "assignees": [self.worker.id],
            "tags": [self.tag.id],
            "project": self.project.id,
        }
        form = TaskForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_required_fields(self):
        """Test form with missing required fields."""
        form_data = {}
        form = TaskForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertIn("description", form.errors)
        self.assertIn("deadline", form.errors)

    def test_deadline_widget(self):
        """Test deadline field has date widget."""
        form = TaskForm()
        self.assertEqual(form.fields["deadline"].widget.input_type, "date")

    def test_assignees_widget(self):
        """Test assignees field has checkbox select multiple widget."""
        form = TaskForm()
        self.assertEqual(
            form.fields["assignees"].widget.__class__.__name__,
            "CheckboxSelectMultiple",
        )

    def test_tags_widget(self):
        """Test tags field has checkbox select multiple widget."""
        form = TaskForm()
        self.assertEqual(
            form.fields["tags"].widget.__class__.__name__, "CheckboxSelectMultiple"
        )


class ProjectFormTest(TestCase):
    """Test ProjectForm."""

    def test_valid_form(self):
        """Test form with valid data."""
        form_data = {
            "name": "Test Project",
            "description": "Test description",
        }
        form = ProjectForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_name(self):
        """Test form with missing name."""
        form_data = {
            "description": "Test description",
        }
        form = ProjectForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_description_optional(self):
        """Test description is optional."""
        form_data = {
            "name": "Test Project",
        }
        form = ProjectForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_description_widget(self):
        """Test description field has textarea widget."""
        form = ProjectForm()
        self.assertEqual(
            form.fields["description"].widget.__class__.__name__, "Textarea"
        )


class TeamFormTest(TestCase):
    """Test TeamForm."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.worker1 = Worker.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.worker2 = Worker.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="pass123",
            first_name="Jane",
            last_name="Smith",
            position=self.position,
        )
        self.project = Project.objects.create(name="Test Project")

    def test_valid_form(self):
        """Test form with valid data."""
        form_data = {
            "name": "Test Team",
            "members": [self.worker1.id, self.worker2.id],
            "project": self.project.id,
        }
        form = TeamForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_name(self):
        """Test form with missing name."""
        form_data = {
            "members": [self.worker1.id],
        }
        form = TeamForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_members_widget(self):
        """Test members field has checkbox select multiple widget."""
        form = TeamForm()
        self.assertEqual(
            form.fields["members"].widget.__class__.__name__, "CheckboxSelectMultiple"
        )

    def test_project_optional(self):
        """Test project is optional."""
        form_data = {
            "name": "Test Team",
            "members": [self.worker1.id],
        }
        form = TeamForm(data=form_data)
        self.assertTrue(form.is_valid())


class TagFormTest(TestCase):
    """Test TagForm."""

    def test_valid_form(self):
        """Test form with valid data."""
        form_data = {
            "name": "urgent",
        }
        form = TagForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_name(self):
        """Test form with missing name."""
        form_data = {}
        form = TagForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class CommentFormTest(TestCase):
    """Test CommentForm."""

    def test_valid_form(self):
        """Test form with valid data."""
        form_data = {
            "content": "This is a test comment",
        }
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_content(self):
        """Test form with missing content."""
        form_data = {}
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)

    def test_content_widget(self):
        """Test content field has textarea widget with correct attributes."""
        form = CommentForm()
        self.assertEqual(form.fields["content"].widget.__class__.__name__, "Textarea")
        self.assertEqual(form.fields["content"].widget.attrs["rows"], 3)
        self.assertEqual(
            form.fields["content"].widget.attrs["placeholder"], "Add a comment..."
        )

    def test_content_label(self):
        """Test content field has correct label."""
        form = CommentForm()
        self.assertEqual(form.fields["content"].label, "Comment")
class RegisterViewTest(TestCase):
    """Test RegisterView."""

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.url = reverse("register")

    def test_register_view_get(self):
        """Test GET request to register view."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/register.html")

    def test_register_view_post_valid(self):
        """Test POST request with valid data."""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "position": self.position.id,
            "password1": "testpass123!@#",
            "password2": "testpass123!@#",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Worker.objects.filter(username="newuser").exists())

    def test_register_view_post_invalid(self):
        """Test POST request with invalid data."""
        data = {
            "username": "newuser",
            "email": "invalid-email",
            "password1": "testpass123!@#",
            "password2": "differentpass",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Worker.objects.filter(username="newuser").exists())


class TaskListViewTest(TestCase):
    """Test TaskListView."""

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.client.login(username="testuser", password="testpass123")
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.project = Project.objects.create(name="Test Project")
        self.url = reverse("task_list")

    def test_task_list_view_requires_login(self):
        """Test task list view requires authentication."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_task_list_view_get(self):
        """Test GET request to task list view."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/task_list.html")

    def test_task_list_filter_by_status_completed(self):
        """Test filtering tasks by completed status."""
        Task.objects.create(
            name="Completed Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            is_completed=True,
            task_type=self.task_type,
            created_by=self.user,
        )
        Task.objects.create(
            name="Incomplete Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            is_completed=False,
            task_type=self.task_type,
            created_by=self.user,
        )

        response = self.client.get(self.url, {"status": "completed"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tasks"]), 1)
        self.assertTrue(response.context["tasks"][0].is_completed)

    def test_task_list_filter_by_priority(self):
        """Test filtering tasks by priority."""
        Task.objects.create(
            name="High Priority",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            priority="High",
            task_type=self.task_type,
            created_by=self.user,
        )
        Task.objects.create(
            name="Low Priority",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            priority="Low",
            task_type=self.task_type,
            created_by=self.user,
        )

        response = self.client.get(self.url, {"priority": "High"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tasks"]), 1)
        self.assertEqual(response.context["tasks"][0].priority, "High")

    def test_task_list_search(self):
        """Test searching tasks."""
        Task.objects.create(
            name="Find Me",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.user,
        )
        Task.objects.create(
            name="Other Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.user,
        )

        response = self.client.get(self.url, {"search": "Find Me"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tasks"]), 1)
        self.assertEqual(response.context["tasks"][0].name, "Find Me")


class TaskCreateViewTest(TestCase):
    """Test TaskCreateView."""

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.client.login(username="testuser", password="testpass123")
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.url = reverse("task_create")

    def test_task_create_view_requires_login(self):
        """Test task create view requires authentication."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_task_create_view_get(self):
        """Test GET request to task create view."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/task_form.html")

    def test_task_create_view_post_valid(self):
        """Test POST request with valid data."""
        data = {
            "name": "New Task",
            "description": "Test description",
            "deadline": (timezone.now().date() + timedelta(days=1)).isoformat(),
            "priority": "High",
            "task_type": self.task_type.id,
            "assignees": [self.user.id],  # Add required assignees
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(name="New Task").exists())

        # Verify created_by is set automatically
        task = Task.objects.get(name="New Task")
        self.assertEqual(task.created_by, self.user)


class TaskUpdateViewTest(TestCase):
    """Test TaskUpdateView."""

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.other_user = Worker.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123",
            first_name="Other",
            last_name="User",
            position=self.position,
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.user,
        )
        self.url = reverse("task_edit", kwargs={"pk": self.task.pk})

    def test_task_update_permission_creator(self):
        """Test task creator can update task."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_task_update_permission_non_creator(self):
        """Test non-creator cannot update task."""
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.get(self.url)
        # Should return 404 because queryset filters by creator
        self.assertEqual(response.status_code, 404)

    def test_task_update_permission_staff(self):
        """Test staff can update any task."""
        self.other_user.is_staff = True
        self.other_user.save()
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class TaskDeleteViewTest(TestCase):
    """Test TaskDeleteView."""

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.other_user = Worker.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123",
            first_name="Other",
            last_name="User",
            position=self.position,
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.user,
        )
        self.url = reverse("task_delete", kwargs={"pk": self.task.pk})

    def test_task_delete_permission_creator(self):
        """Test task creator can delete task."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_task_delete_permission_non_creator(self):
        """Test non-creator cannot delete task."""
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.get(self.url)
        # Should return 404 because queryset filters by creator
        self.assertEqual(response.status_code, 404)


class TaskToggleStatusViewTest(TestCase):
    """Test task_toggle_status view."""

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.client.login(username="testuser", password="testpass123")
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            is_completed=False,
            task_type=self.task_type,
            created_by=self.user,
        )
        self.url = reverse("task_toggle_status", kwargs={"pk": self.task.pk})

    def test_toggle_status_incomplete_to_complete(self):
        """Test toggling task from incomplete to complete."""
        self.assertFalse(self.task.is_completed)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)

    def test_toggle_status_complete_to_incomplete(self):
        """Test toggling task from complete to incomplete."""
        self.task.is_completed = True
        self.task.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()
        self.assertFalse(self.task.is_completed)


class DashboardViewTest(TestCase):
    """Test dashboard view."""

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.client.login(username="testuser", password="testpass123")
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.url = reverse("dashboard")

    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_dashboard_view_get(self):
        """Test GET request to dashboard."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/dashboard.html")

    def test_dashboard_statistics(self):
        """Test dashboard displays correct statistics."""
        # Create tasks
        Task.objects.create(
            name="Completed",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            is_completed=True,
            task_type=self.task_type,
            created_by=self.user,
        )
        Task.objects.create(
            name="Incomplete",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            is_completed=False,
            task_type=self.task_type,
            created_by=self.user,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.context["total_tasks"], 2)
        self.assertEqual(response.context["completed_tasks"], 1)
        self.assertEqual(response.context["incomplete_tasks"], 1)


class ProjectViewsTest(TestCase):
    """Test project views."""

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.client.login(username="testuser", password="testpass123")

    def test_project_list_view(self):
        """Test project list view."""
        Project.objects.create(name="Project 1")
        Project.objects.create(name="Project 2")

        response = self.client.get(reverse("project_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["projects"]), 2)

    def test_project_create_view(self):
        """Test project create view."""
        data = {"name": "New Project", "description": "Test description"}
        response = self.client.post(reverse("project_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(name="New Project").exists())

    def test_project_detail_view(self):
        """Test project detail view."""
        project = Project.objects.create(name="Test Project")
        response = self.client.get(reverse("project_detail", kwargs={"pk": project.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["project"], project)


class TeamViewsTest(TestCase):
    """Test team views."""

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.client.login(username="testuser", password="testpass123")

    def test_team_list_view(self):
        """Test team list view."""
        Team.objects.create(name="Team 1")
        Team.objects.create(name="Team 2")

        response = self.client.get(reverse("team_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["teams"]), 2)

    def test_team_create_view(self):
        """Test team create view."""
        data = {"name": "New Team", "members": [self.user.id]}
        response = self.client.post(reverse("team_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Team.objects.filter(name="New Team").exists())


class NotificationViewsTest(TestCase):
    """Test notification views."""

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.client.login(username="testuser", password="testpass123")
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.task = Task.objects.create(
            name="Test Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.user,
        )

    def test_notification_list_view(self):
        """Test notification list view."""
        Notification.objects.create(
            recipient=self.user,
            notification_type="task_assigned",
            title="Test",
            message="Test message",
            task=self.task,
        )

        response = self.client.get(reverse("notifications_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["notifications"]), 1)

    def test_notification_mark_read(self):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type="task_assigned",
            title="Test",
            message="Test message",
            task=self.task,
            is_read=False,
        )

        url = reverse("notification_mark_read", kwargs={"pk": notification.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_notification_mark_all_read(self):
        """Test marking all notifications as read."""
        Notification.objects.create(
            recipient=self.user,
            notification_type="task_assigned",
            title="Test 1",
            message="Test",
            task=self.task,
            is_read=False,
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type="task_assigned",
            title="Test 2",
            message="Test",
            task=self.task,
            is_read=False,
        )

        response = self.client.get(reverse("notification_mark_all_read"))
        self.assertEqual(response.status_code, 302)

        unread_count = Notification.objects.filter(
            recipient=self.user, is_read=False
        ).count()
        self.assertEqual(unread_count, 0)


class PositionViewsTest(TestCase):
    """Test position views (superuser only)."""

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.superuser = Worker.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            first_name="Admin",
            last_name="User",
        )
        self.regular_user = Worker.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="pass123",
            first_name="Regular",
            last_name="User",
            position=self.position,
        )

    def test_position_list_requires_superuser(self):
        """Test position list requires superuser."""
        self.client.login(username="regular", password="pass123")
        response = self.client.get(reverse("position_list"))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_position_list_superuser_access(self):
        """Test superuser can access position list."""
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(reverse("position_list"))
        self.assertEqual(response.status_code, 200)

    def test_position_create_requires_superuser(self):
        """Test position create requires superuser."""
        self.client.login(username="regular", password="pass123")
        response = self.client.get(reverse("position_create"))
        self.assertEqual(response.status_code, 403)


class WorkerManagementViewsTest(TestCase):
    """Test worker management views (superuser only)."""

    def setUp(self):
        self.client = Client()
        self.position = Position.objects.create(name="Developer")
        self.superuser = Worker.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            first_name="Admin",
            last_name="User",
        )
        self.regular_user = Worker.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="pass123",
            first_name="Regular",
            last_name="User",
            position=self.position,
        )

    def test_worker_list_requires_superuser(self):
        """Test worker list requires superuser."""
        self.client.login(username="regular", password="pass123")
        response = self.client.get(reverse("worker_list"))
        self.assertEqual(response.status_code, 403)

    def test_worker_list_superuser_access(self):
        """Test superuser can access worker list."""
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(reverse("worker_list"))
        self.assertEqual(response.status_code, 200)

    def test_worker_update_requires_superuser(self):
        """Test worker update requires superuser."""
        self.client.login(username="regular", password="pass123")
        url = reverse("worker_edit", kwargs={"pk": self.regular_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
class TaskPostSaveSignalTest(TestCase):
    """Test task_post_save signal."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.worker = Worker.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")

    def test_activity_log_created_on_task_creation(self):
        """Test activity log is created when task is created."""
        initial_count = ActivityLog.objects.count()

        task = Task.objects.create(
            name="Test Task",
            description="Test description",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.worker,
        )

        # Check activity log was created
        self.assertEqual(ActivityLog.objects.count(), initial_count + 1)

        # Verify activity log details
        log = ActivityLog.objects.filter(task=task, activity_type="created").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.worker)
        self.assertIn(task.name, log.description)

    def test_activity_log_created_on_task_completion(self):
        """Test activity log is created when task is completed."""
        task = Task.objects.create(
            name="Test Task",
            description="Test description",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.worker,
            is_completed=False,
        )

        # Clear existing logs
        initial_count = ActivityLog.objects.filter(
            task=task, activity_type="completed"
        ).count()

        # Mark task as completed
        task.is_completed = True
        task.save()

        # Check activity log was created
        completed_logs = ActivityLog.objects.filter(
            task=task, activity_type="completed"
        )
        self.assertEqual(completed_logs.count(), initial_count + 1)

        # Verify activity log details
        log = completed_logs.first()
        self.assertIsNotNone(log)
        self.assertIn(task.name, log.description)


class TaskAssigneesChangedSignalTest(TestCase):
    """Test task_assignees_changed signal."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.worker1 = Worker.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass123",
            first_name="John",
            last_name="Doe",
            position=self.position,
        )
        self.worker2 = Worker.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="pass123",
            first_name="Jane",
            last_name="Smith",
            position=self.position,
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.task = Task.objects.create(
            name="Test Task",
            description="Test description",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.worker1,
        )

    def test_notification_created_on_assignment(self):
        """Test notification is created when worker is assigned to task."""
        initial_count = Notification.objects.filter(recipient=self.worker2).count()

        # Assign worker to task
        self.task.assignees.add(self.worker2)

        # Check notification was created
        notifications = Notification.objects.filter(recipient=self.worker2)
        self.assertEqual(notifications.count(), initial_count + 1)

        # Verify notification details
        notification = notifications.filter(notification_type="task_assigned").first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.task, self.task)
        self.assertIn(self.task.name, notification.message)
        self.assertFalse(notification.is_read)

    def test_activity_log_created_on_assignment(self):
        """Test activity log is created when worker is assigned to task."""
        initial_count = ActivityLog.objects.filter(
            task=self.task, activity_type="assigned"
        ).count()

        # Assign worker to task
        self.task.assignees.add(self.worker2)

        # Check activity log was created
        logs = ActivityLog.objects.filter(task=self.task, activity_type="assigned")
        self.assertEqual(logs.count(), initial_count + 1)

        # Verify activity log details
        log = logs.filter(user=self.worker2).first()
        self.assertIsNotNone(log)
        self.assertIn(self.worker2.get_full_name(), log.description)

    def test_activity_log_created_on_unassignment(self):
        """Test activity log is created when worker is removed from task."""
        # First assign worker
        self.task.assignees.add(self.worker2)

        initial_count = ActivityLog.objects.filter(
            task=self.task, activity_type="unassigned"
        ).count()

        # Remove worker from task
        self.task.assignees.remove(self.worker2)

        # Check activity log was created
        logs = ActivityLog.objects.filter(task=self.task, activity_type="unassigned")
        self.assertEqual(logs.count(), initial_count + 1)

        # Verify activity log details
        log = logs.filter(user=self.worker2).first()
        self.assertIsNotNone(log)
        self.assertIn(self.worker2.get_full_name(), log.description)

    def test_multiple_assignees_create_multiple_notifications(self):
        """Test multiple workers get notifications when assigned."""
        initial_count1 = Notification.objects.filter(recipient=self.worker1).count()
        initial_count2 = Notification.objects.filter(recipient=self.worker2).count()

        # Assign both workers
        self.task.assignees.add(self.worker1, self.worker2)

        # Check both got notifications
        self.assertEqual(
            Notification.objects.filter(recipient=self.worker1).count(),
            initial_count1 + 1,
        )
        self.assertEqual(
            Notification.objects.filter(recipient=self.worker2).count(),
            initial_count2 + 1,
        )


class CommentPostSaveSignalTest(TestCase):
    """Test comment_post_save signal."""

    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.task_creator = Worker.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="pass123",
            first_name="Task",
            last_name="Creator",
            position=self.position,
        )
        self.assignee1 = Worker.objects.create_user(
            username="assignee1",
            email="assignee1@example.com",
            password="pass123",
            first_name="Assignee",
            last_name="One",
            position=self.position,
        )
        self.assignee2 = Worker.objects.create_user(
            username="assignee2",
            email="assignee2@example.com",
            password="pass123",
            first_name="Assignee",
            last_name="Two",
            position=self.position,
        )
        self.commenter = Worker.objects.create_user(
            username="commenter",
            email="commenter@example.com",
            password="pass123",
            first_name="Comment",
            last_name="Author",
            position=self.position,
        )
        self.task_type = TaskType.objects.create(name="Bug Fix")
        self.task = Task.objects.create(
            name="Test Task",
            description="Test description",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.task_creator,
        )
        self.task.assignees.add(self.assignee1, self.assignee2)

    def test_activity_log_created_on_comment(self):
        """Test activity log is created when comment is added."""
        initial_count = ActivityLog.objects.filter(
            task=self.task, activity_type="commented"
        ).count()

        # Create comment
        comment = Comment.objects.create(
            task=self.task, author=self.commenter, content="Test comment"
        )

        # Check activity log was created
        logs = ActivityLog.objects.filter(task=self.task, activity_type="commented")
        self.assertEqual(logs.count(), initial_count + 1)

        # Verify activity log details
        log = logs.filter(user=self.commenter).first()
        self.assertIsNotNone(log)
        self.assertIn(self.commenter.get_full_name(), log.description)

    def test_notifications_created_for_assignees(self):
        """Test notifications are created for assignees when comment is added."""
        # Comment author should not receive notification
        initial_count1 = Notification.objects.filter(recipient=self.assignee1).count()
        initial_count2 = Notification.objects.filter(recipient=self.assignee2).count()

        # Create comment
        Comment.objects.create(
            task=self.task, author=self.commenter, content="Test comment"
        )

        # Check notifications were created for assignees
        self.assertEqual(
            Notification.objects.filter(recipient=self.assignee1).count(),
            initial_count1 + 1,
        )
        self.assertEqual(
            Notification.objects.filter(recipient=self.assignee2).count(),
            initial_count2 + 1,
        )

        # Verify notification details
        notification = Notification.objects.filter(
            recipient=self.assignee1, notification_type="task_commented"
        ).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.task, self.task)
        self.assertIn(self.commenter.get_full_name(), notification.message)

    def test_comment_author_does_not_receive_notification(self):
        """Test comment author does not receive notification."""
        # Assignee1 is both assignee and commenter
        initial_count = Notification.objects.filter(
            recipient=self.assignee1, notification_type="task_commented"
        ).count()

        # Create comment by assignee1
        Comment.objects.create(
            task=self.task, author=self.assignee1, content="Test comment"
        )

        # Assignee1 should not receive notification for their own comment
        new_count = Notification.objects.filter(
            recipient=self.assignee1, notification_type="task_commented"
        ).count()
        self.assertEqual(new_count, initial_count)

    def test_task_creator_receives_notification(self):
        """Test task creator receives notification if not an assignee."""
        initial_count = Notification.objects.filter(recipient=self.task_creator).count()

        # Create comment
        Comment.objects.create(
            task=self.task, author=self.commenter, content="Test comment"
        )

        # Task creator should receive notification
        notifications = Notification.objects.filter(recipient=self.task_creator)
        self.assertEqual(notifications.count(), initial_count + 1)

        # Verify notification details
        notification = notifications.filter(notification_type="task_commented").first()
        self.assertIsNotNone(notification)
        self.assertIn("your task", notification.message)

    def test_task_creator_as_assignee_receives_one_notification(self):
        """Test task creator who is also assignee receives only one notification."""
        # Create new task where creator is also assignee
        new_task = Task.objects.create(
            name="New Task",
            description="Test",
            deadline=timezone.now().date() + timedelta(days=1),
            task_type=self.task_type,
            created_by=self.task_creator,
        )
        new_task.assignees.add(self.task_creator)

        initial_count = Notification.objects.filter(
            recipient=self.task_creator, notification_type="task_commented"
        ).count()

        # Create comment
        Comment.objects.create(
            task=new_task, author=self.commenter, content="Test comment"
        )

        # Task creator should receive only one notification
        new_count = Notification.objects.filter(
            recipient=self.task_creator, notification_type="task_commented"
        ).count()
        self.assertEqual(new_count, initial_count + 1)
