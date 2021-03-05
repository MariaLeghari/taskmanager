"""
Task Manager Serializers
"""
from rest_framework import serializers
from rest_framework.serializers import raise_errors_on_nested_writes
from rest_framework.utils import model_meta

from taskmanager_api.models import Comment, EventLog, User, RejectedTask, Task, STATUS_CHOICES


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for all user details
    """
    class Meta:
        model = User
        fields = '__all__'


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for create new user
    """
    email = serializers.EmailField(required=True)
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, min_length=8, max_length=14, write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.is_active = False
        instance.save()
        return instance


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer to update the user general information.
    """

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'profile_image')


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    model = User
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


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
            instance.request_status = STATUS_CHOICES.PENDING

        instance.save()

        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)

        return instance


class RejectedTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for rejected task
    """
    assignee = serializers.Field(default=serializers.CurrentUserDefault(), required=False)

    class Meta:
        model = RejectedTask
        fields = '__all__'
