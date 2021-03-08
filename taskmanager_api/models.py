"""
Task Manager Models
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from model_utils import Choices
from model_utils.models import TimeStampedModel

from core.models import User

STATUS_CHOICES = Choices('PENDING', 'ACCEPT', 'REJECT')


class Task(TimeStampedModel):
    """
    Task Model
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, name='creator')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assignee')
    notifier = models.ManyToManyField(User, blank=True, related_name='notifier')
    request_status = models.CharField(max_length=7, choices=STATUS_CHOICES, default=STATUS_CHOICES.PENDING)

    def __str__(self):
        return self.title

    def accept_task(self):
        self.request_status = STATUS_CHOICES.ACCEPT
        self.save()

    def reject_task(self):
        self.request_status = STATUS_CHOICES.REJECT
        self.save()

    def pending_task(self):
        self.pending_task = STATUS_CHOICES.PENDING
        self.save()


class RejectedTask(TimeStampedModel):
    """
    Task Rejected by Assignee
    """
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reject_by_assignee')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='rejected_task')
    reason = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.assignee.username} rejected task {self.task.id}"


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
