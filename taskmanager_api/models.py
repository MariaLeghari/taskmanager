"""
Task Manager Models
"""
from django.contrib.auth.models import AbstractUser
from django.contrib.sites.shortcuts import get_current_site
from django.db import models
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from model_utils import Choices
from model_utils.models import TimeStampedModel

from taskmanager_api.tokens import AccountActivationTokenGenerator

STATUS_CHOICES = Choices('PENDING', 'ACCEPT', 'REJECT')


class User(AbstractUser):
    """
    User Model
    Extra fields in default user model
    """
    email = models.EmailField(unique=True)
    profile_image = models.ImageField(upload_to='profile_pictures/', blank=True)

    def send_activation_email(self, request):
        """ send activation link to the user email """
        current_site = get_current_site(request)
        subject = 'Activate Your Task Manager Account'
        from django.utils.encoding import force_bytes
        message = render_to_string('taskmanager_api/acc_active_email.html', {
            'user': self,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(self.pk)),
            'token': AccountActivationTokenGenerator().make_token(self),
        })
        self.email_user(subject, message)


class Task(TimeStampedModel):
    """
    Task Model
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
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

    def comments(self):
        return self.comment_set.all()

    def event_logs(self):
        return self.eventlog_set.all()


class RejectedTask(TimeStampedModel):
    """
    Task Rejected by Assignee
    """
    assignee = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    reason = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.assignee.username} rejected task {self.task.id}"


class Comment(TimeStampedModel):
    """
    Comment Model
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} commented on {self.task.title}"


class EventLog(models.Model):
    """
    Event Log Model
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    description = models.TextField()

    def __str__(self):
        return self.description
