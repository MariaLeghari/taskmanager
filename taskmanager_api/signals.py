""" Task Manager Api Signals """
from django.dispatch import Signal, receiver

from core.utils import STATUS_CHOICES, REQUEST_CHOICES

check_task_status = Signal(providing_args=['task'])


@receiver(check_task_status)
def check_task_assignee_action(sender, task, **kwargs):
    """ Change task status according to assignees request status"""
    assignees = task.task_assignee.all()
    accept_request_assignees = assignees.filter(request_status=REQUEST_CHOICES.ACCEPT)
    pending_request_assignees = assignees.filter(request_status=REQUEST_CHOICES.PENDING)
    if accept_request_assignees:
        if task.task_status != STATUS_CHOICES.ACCEPTED:
            task.change_task_status(STATUS_CHOICES.ACCEPTED)
    elif pending_request_assignees:
        if task.task_status != STATUS_CHOICES.PENDING:
            task.change_task_status(STATUS_CHOICES.PENDING)
    else:
        if task.task_status != STATUS_CHOICES.REJECTED:
            task.change_task_status(STATUS_CHOICES.REJECTED)
