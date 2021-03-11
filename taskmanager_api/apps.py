from django.apps import AppConfig

from taskmanager_api import signals


class TaskmanagerApiConfig(AppConfig):
    name = 'taskmanager_api'

    def ready(self):
        signals.check_task_status.connect(signals.check_task_assignee_action)
