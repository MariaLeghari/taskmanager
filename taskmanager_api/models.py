"""
Task Manager Models
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from model_utils.models import TimeStampedModel

from core.models import User
from core.utils import REQUEST_CHOICES, STATUS_CHOICES
from taskmanager_api.signals import check_task_status


class Task(TimeStampedModel):
    """
    Task Model
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, name='creator')
    notifier = models.ManyToManyField(User, blank=True, related_name='notifier')
    task_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_CHOICES.UNASSIGNED)

    def __str__(self):
        return self.title

    def change_task_status(self, status):
        self.task_status = status
        self.save()


class TaskAssignees(TimeStampedModel):
    """
    Assignees assigned to task.
    """
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignee')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_assignee')
    reason = models.CharField(max_length=200, blank=True, null=True)
    request_status = models.CharField(max_length=7, choices=REQUEST_CHOICES, default=REQUEST_CHOICES.PENDING)

    def __str__(self):
        return f"{self.task.creator.username} assign task to {self.assignee.username}"

    class Meta:
        unique_together = ['task', 'assignee']

    def change_request_status(self, status, reason=None):
        self.request_status = status
        self.reason = reason
        self.save()
        check_task_status.send(sender=self.__class__, task=self.task)


class Comment(TimeStampedModel):
    """
    Comment Model
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comment')

    def __str__(self):
        return f"{self.user.username} commented on {self.task.title}"


class EventLog(models.Model):
    """
    Event Log Model
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='event_log')
    description = models.TextField()

    def __str__(self):
        return self.description
