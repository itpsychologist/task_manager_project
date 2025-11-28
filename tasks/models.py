from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_deadline(value):
    if value < timezone.now().date():
        raise ValidationError('Дедлайн не може бути в минулому')


class Position(models.Model):
    """Посада працівника"""
    name = models.CharField(
        max_length=100, unique=True, verbose_name='Назва посади'
    )

    class Meta:
        verbose_name = 'Посада'
        verbose_name_plural = 'Посади'

    def __str__(self):
        return self.name


class Worker(AbstractUser):
    """Працівник (розширена модель користувача)"""
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        related_name='workers',
        verbose_name='Посада'
    )
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name='Email'
    )
    first_name = models.CharField(max_length=150, verbose_name='Ім\'я')
    last_name = models.CharField(max_length=150, verbose_name='Прізвище')

    class Meta:
        verbose_name = 'Працівник'
        verbose_name_plural = 'Працівники'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.position})"

    def get_completed_tasks(self):
        """Повертає виконані завдання працівника"""
        return self.assigned_tasks.filter(is_completed=True)

    def get_incomplete_tasks(self):
        """Повертає невиконані завдання працівника"""
        return self.assigned_tasks.filter(is_completed=False)

    def get_unread_notifications_count(self):
        """Повертає кількість непрочитаних нотифікацій"""
        return self.notifications.filter(is_read=False).count()

    def get_unread_notifications(self):
        """Повертає непрочитані нотифікації"""
        return self.notifications.filter(is_read=False).order_by('-created_at')


class TaskType(models.Model):
    """Тип завдання"""
    name = models.CharField(
        max_length=100, unique=True, verbose_name='Назва типу'
    )

    class Meta:
        verbose_name = 'Тип завдання'
        verbose_name_plural = 'Типи завдань'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Тег для завдань"""
    name = models.CharField(
        max_length=100, unique=True, verbose_name='Назва тегу'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Project(models.Model):
    """Проєкт"""
    name = models.CharField(max_length=200, verbose_name='Назва проєкту')
    description = models.TextField(blank=True, verbose_name='Опис')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата створення'
    )

    class Meta:
        verbose_name = 'Проєкт'
        verbose_name_plural = 'Проєкти'

    def __str__(self):
        return self.name


class Team(models.Model):
    """Команда"""
    name = models.CharField(max_length=200, verbose_name='Назва команди')
    members = models.ManyToManyField(
        Worker,
        related_name='teams',
        verbose_name='Члени команди'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='teams',
        null=True,
        blank=True,
        verbose_name='Проєкт'
    )

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команди'

    def __str__(self):
        return self.name


class Task(models.Model):
    """Завдання"""
    PRIORITY_CHOICES = [
        ('Urgent', 'Термінове'),
        ('High', 'Високий'),
        ('Medium', 'Середній'),
        ('Low', 'Низький'),
    ]

    name = models.CharField(max_length=200, verbose_name='Назва завдання')
    description = models.TextField(verbose_name='Опис')
    deadline = models.DateField(
        verbose_name='Дедлайн', validators=[validate_deadline]
    )
    is_completed = models.BooleanField(default=False, verbose_name='Виконано')
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='Medium',
        verbose_name='Пріоритет'
    )
    task_type = models.ForeignKey(
        TaskType,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tasks',
        verbose_name='Тип завдання'
    )
    assignees = models.ManyToManyField(
        Worker,
        related_name='assigned_tasks',
        verbose_name='Виконавці'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='tasks',
        blank=True,
        verbose_name='Теги'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True,
        verbose_name='Проєкт'
    )
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name='Створив'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата створення'
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='Дата оновлення'
    )

    class Meta:
        verbose_name = 'Завдання'
        verbose_name_plural = 'Завдання'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_priority_display()})"

    def mark_as_completed(self):
        """Позначити завдання як виконане"""
        self.is_completed = True
        self.save()

    def mark_as_incomplete(self):
        """Позначити завдання як невиконане"""
        self.is_completed = False
        self.save()

    def get_activity_log(self):
        """Повертає всю активність для завдання"""
        return self.activity_logs.all().order_by('-created_at')

    def get_comments(self):
        """Повертає всі коментарі для завдання"""
        return self.comments.all().order_by('-created_at')

    def get_completion_percentage(self):
        """Повертає відсоток виконання (0 або 100)"""
        return 100 if self.is_completed else 0


class Comment(models.Model):
    """Коментар до завдання"""
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Завдання'
    )
    author = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    content = models.TextField(verbose_name='Зміст коментаря')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата створення'
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='Дата оновлення'
    )

    class Meta:
        verbose_name = 'Коментар'
        verbose_name_plural = 'Коментарі'
        ordering = ['-created_at']

    def __str__(self):
        return f"Коментар від {self.author} до {self.task.name}"


class ActivityLog(models.Model):
    """Журнал активності для відстеження змін"""
    ACTIVITY_TYPES = [
        ('created', 'Створено'),
        ('updated', 'Оновлено'),
        ('completed', 'Виконано'),
        ('reopened', 'Відновлено'),
        ('assigned', 'Призначено'),
        ('unassigned', 'Знято призначення'),
        ('commented', 'Додано коментар'),
        ('deleted', 'Видалено'),
    ]

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        null=True,
        blank=True,
        verbose_name='Завдання'
    )
    user = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities',
        verbose_name='Користувач'
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
        verbose_name='Тип активності'
    )
    description = models.TextField(verbose_name='Опис')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата створення'
    )

    class Meta:
        verbose_name = 'Запис активності'
        verbose_name_plural = 'Журнал активності'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.description}"


class Notification(models.Model):
    """Нотифікація для користувача"""
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Призначено завдання'),
        ('task_completed', 'Завдання виконано'),
        ('task_commented', 'Новий коментар'),
        ('deadline_approaching', 'Наближається дедлайн'),
        ('task_updated', 'Завдання оновлено'),
    ]

    recipient = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Отримувач'
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        verbose_name='Тип нотифікації'
    )
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Повідомлення')
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        verbose_name='Завдання'
    )
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата створення'
    )

    class Meta:
        verbose_name = 'Нотифікація'
        verbose_name_plural = 'Нотифікації'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} для {self.recipient}"

    def mark_as_read(self):
        """Позначити як прочитане"""
        self.is_read = True
        self.save()
