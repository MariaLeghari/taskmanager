"""
Task Manager Serializers
"""
from rest_framework import serializers

from taskmanager_api.models import Comment, EventLog, TaskAssignees, Task


class EventLogSerializer(serializers.ModelSerializer):
    """
    Serializer for event log
    """

    class Meta:
        model = EventLog
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for comments
    """

    class Meta:
        model = Comment
        fields = '__all__'


class TaskAssigneesSerializer(serializers.ModelSerializer):
    """
    Serializer to view assignees
    """

    class Meta:
        model = TaskAssignees
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for task
    """
    task_assignee = TaskAssigneesSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, required=False)
    event_logs = EventLogSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
