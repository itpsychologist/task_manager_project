from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Task, Comment, ActivityLog, Notification


@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    """Create activity log when a task is created or updated."""
    if created:
        ActivityLog.objects.create(
            task=instance,
            user=instance.created_by,
            activity_type="created",
            description=f'Task "{instance.name}" created',
        )
    else:
        # Check if status changed
        if instance.is_completed:
            ActivityLog.objects.create(
                task=instance,
                user=None,  # Will be set in view
                activity_type="completed",
                description=f'Task "{instance.name}" completed',
            )


@receiver(m2m_changed, sender=Task.assignees.through)
def task_assignees_changed(sender, instance, action, pk_set, **kwargs):
    """Create notifications when a task is assigned."""
    if action == "post_add":
        from .models import Worker

        for worker_id in pk_set:
            worker = Worker.objects.get(pk=worker_id)
            Notification.objects.create(
                recipient=worker,
                notification_type="task_assigned",
                title="New Task",
                message=f"You have been assigned a task: {instance.name}",
                task=instance,
            )
            ActivityLog.objects.create(
                task=instance,
                user=worker,
                activity_type="assigned",
                description=f"{worker.get_full_name()} assigned to task",
            )
    elif action == "post_remove":
        from .models import Worker

        for worker_id in pk_set:
            worker = Worker.objects.get(pk=worker_id)
            ActivityLog.objects.create(
                task=instance,
                user=worker,
                activity_type="unassigned",
                description=f"{worker.get_full_name()} removed from task",
            )


@receiver(post_save, sender=Comment)
def comment_post_save(sender, instance, created, **kwargs):
    """Create notifications and activity log when a comment is added."""
    if created:
        # Create activity log
        ActivityLog.objects.create(
            task=instance.task,
            user=instance.author,
            activity_type="commented",
            description=f"{instance.author.get_full_name()} added a comment",
        )

        # Create notifications for all assignees (except comment author)
        for assignee in instance.task.assignees.exclude(id=instance.author.id):
            Notification.objects.create(
                recipient=assignee,
                notification_type="task_commented",
                title="New Comment",
                message=(
                    f"{instance.author.get_full_name()} "
                    f"commented on task: {instance.task.name}"
                ),
                task=instance.task,
            )

        # Also notify task creator if they are not the comment author
        if (instance.task.created_by
                and instance.task.created_by != instance.author):
            if not instance.task.assignees.filter(
                id=instance.task.created_by.id
            ).exists():
                Notification.objects.create(
                    recipient=instance.task.created_by,
                    notification_type="task_commented",
                    title="New Comment",
                    message=(
                        f"{instance.author.get_full_name()} "
                        f"commented on your task: {instance.task.name}"
                    ),
                    task=instance.task,
                )
