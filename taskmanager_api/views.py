"""
Task Manager Views
"""
from django.core.mail import send_mail
from django.db.models import Q
from django.dispatch import receiver
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from django_rest_passwordreset.signals import reset_password_token_created
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status

from taskmanager_api.models import Comment, EventLog, Task, RejectedTask
from taskmanager_api.serializers import (
    CommentSerializer,
    RejectedTaskSerializer,
    TaskSerializer
)


class TaskViewSet(ModelViewSet):
    """
    list:
    Return all the task of the current user.

    create:
    Create a new task of current user.

    update:
    Update the information of a specific task.

    destroy:
    Delete a specific task.
    """
    model = Task
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated,)
    filterset_fields = ['creator', 'assignee', 'notifier', 'request_status']

    def get_queryset(self):
        return Task.objects.filter(
            Q(creator=self.request.user) | Q(Q(assignee__id=self.request.user.id), ~Q(request_status='REJECT')) |
            Q(notifier__id=self.request.user.id)
        ).distinct()

    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,)
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = TaskSerializer(self.filter_queryset(queryset), many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        task = serializer.data
        EventLog(description=f"{request.user.username} created task ", task_id=task['id']).save()
        return Response(task, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.creator.id == request.user.id:
            self.perform_destroy(instance)
            return Response({'data': 'successfully deleted'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.creator.id == request.user.id:
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
            EventLog(description=f"{request.user.username} updated the task.", task_id=serializer.data['id']).save()
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class AcceptTask(APIView):
    """
    Change request_status to accept of the given task.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        task = Task.objects.filter(id=request.data.get('task')).first()
        if task and task.assignee.id == request.user.id:
            task.accept_task()
            EventLog(description=f"{request.user.username} accepted the task.", task_id=task.id).save()
            return Response({'data': 'successfully accepted'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class RejectTask(ListCreateAPIView):
    """
    get:
    Return a list of all the rejected task by current user.

    post:
    Create a new reject task of the current user on a specific task and change the task request_status to reject.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = RejectedTaskSerializer

    def get_queryset(self):
        return RejectedTask.objects.filter(assignee__id=self.request.user.id)

    def post(self, request, *args, **kwargs):
        task = Task.objects.filter(id=request.data.get('task')).first()
        if task and request.user.id == task.assignee.id:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            task.reject_task()
            headers = self.get_success_headers(serializer.data)
            EventLog(description=f"{request.user.username} rejected task request.", task_id=task.id).save()
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class CommentViewSet(ModelViewSet):
    """
    list:
    Return a list of all the existing comments of specific task.

    create:
    Create a new comment on a specific task by user/assignee.

    update:
    Update the information of the comment.

    delete:
    Delete the comment.
    """
    model = Comment
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Comment.objects.filter(task__id=self.request.data.get('task'))

    def create(self, request, *args, **kwargs):
        task = Task.objects.filter(id=request.data.get('task')).first()
        user = User.objects.filter(id=request.data.get('user')).first()
        if task.assignee.id == user.id:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            EventLog(description=f"{request.user.username} commented on the task.", task_id=task.id).save()
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user.id == request.user.id:
            self.perform_destroy(instance)
            return Response({'data': 'successfully deleted'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user.id == request.user.id:
            serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
