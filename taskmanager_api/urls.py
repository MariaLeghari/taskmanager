"""
Task Manager API URL Configuration
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from taskmanager_api.views import (
    AcceptTask,
    CommentViewSet,
    RejectTask,
    TaskAssigneesList,
    TaskViewSet
)

router = DefaultRouter()
router.register('tasks', TaskViewSet, basename='tasks')
router.register('comments', CommentViewSet, basename='comments')

urlpatterns = [
    path('task_assignee_list/', TaskAssigneesList.as_view(), name='task_assignee_list'),
    path('reject_task/', RejectTask.as_view(), name='reject_task'),
    path('accept_task/', AcceptTask.as_view(), name='accept_task'),
]

urlpatterns += router.urls
