"""
Task Manager Serializers
"""
from rest_framework import serializers
from rest_framework.serializers import raise_errors_on_nested_writes
from rest_framework.utils import model_meta

from core.utils import STATUS_CHOICES
from taskmanager_api.models import Comment, EventLog, RejectedTask, Task


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


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for task
    """
    comments = CommentSerializer(many=True, required=False)
    event_logs = EventLogSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = '__all__'

    def update(self, instance, validated_data):
        raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        new_assignee = validated_data.get('assignee')
        old_assignee = instance.assignee

        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)

        if new_assignee and new_assignee != old_assignee:
            instance.change_task_status(STATUS_CHOICES.PENDING)

        instance.save()

        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)

        return instance


class RejectedTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for rejected task
    """
    assignee = serializers.HiddenField(default=serializers.CurrentUserDefault(), required=False)

    class Meta:
        model = RejectedTask
        fields = '__all__'
