from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Task, Comment, ActivityLog, Notification


@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    """Створює запис активності при створенні або оновленні завдання"""
    if created:
        ActivityLog.objects.create(
            task=instance,
            user=instance.created_by,
            activity_type='created',
            description=f'Завдання "{instance.name}" створено'
        )
    else:
        # Перевіряємо, чи змінився статус
        if instance.is_completed:
            ActivityLog.objects.create(
                task=instance,
                user=None,  # Буде встановлено у view
                activity_type='completed',
                description=f'Завдання "{instance.name}" виконано'
            )


@receiver(m2m_changed, sender=Task.assignees.through)
def task_assignees_changed(sender, instance, action, pk_set, **kwargs):
    """Створює нотифікації при призначенні завдання"""
    if action == 'post_add':
        from .models import Worker
        for worker_id in pk_set:
            worker = Worker.objects.get(pk=worker_id)
            Notification.objects.create(
                recipient=worker,
                notification_type='task_assigned',
                title='Нове завдання',
                message=f'Вам призначено завдання: {instance.name}',
                task=instance
            )
            ActivityLog.objects.create(
                task=instance,
                user=worker,
                activity_type='assigned',
                description=f'{worker.get_full_name()} призначено до завдання'
            )
    elif action == 'post_remove':
        from .models import Worker
        for worker_id in pk_set:
            worker = Worker.objects.get(pk=worker_id)
            ActivityLog.objects.create(
                task=instance,
                user=worker,
                activity_type='unassigned',
                description=f'{worker.get_full_name()} знято з завдання'
            )


@receiver(post_save, sender=Comment)
def comment_post_save(sender, instance, created, **kwargs):
    """Створює нотифікації та запис активності при додаванні коментаря"""
    if created:
        # Створюємо запис активності
        ActivityLog.objects.create(
            task=instance.task,
            user=instance.author,
            activity_type='commented',
            description=f'{instance.author.get_full_name()} додав коментар'
        )

        # Створюємо нотифікації для всіх виконавців (крім автора коментаря)
        for assignee in instance.task.assignees.exclude(id=instance.author.id):
            Notification.objects.create(
                recipient=assignee,
                notification_type='task_commented',
                title='Новий коментар',
                message=(
                    f'{instance.author.get_full_name()} '
                    f'прокоментував завдання: {instance.task.name}'
                ),
                task=instance.task
            )

        # Також нотифікуємо автора завдання, якщо він не є автором коментаря
        if (
            instance.task.created_by
            and instance.task.created_by != instance.author
        ):
            if not instance.task.assignees.filter(
                id=instance.task.created_by.id
            ).exists():
                Notification.objects.create(
                    recipient=instance.task.created_by,
                    notification_type='task_commented',
                    title='Новий коментар',
                    message=(
                        f'{instance.author.get_full_name()} '
                        f'прокоментував ваше завдання: {instance.task.name}'
                    ),
                    task=instance.task
                )
