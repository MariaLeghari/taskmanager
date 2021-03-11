"""
Task Manager Views
"""
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status

from core.models import User
from core.utils import STATUS_CHOICES, REQUEST_CHOICES
from taskmanager_api.models import Comment, EventLog, Task, TaskAssignees
from taskmanager_api.serializers import (
    CommentSerializer,
    TaskAssigneesSerializer,
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
    filterset_fields = ['creator', 'notifier', 'task_status']

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Task.objects.all()
        else:
            return Task.objects.filter(
                Q(creator=self.request.user) |
                Q(task_assignee__assignee_id=self.request.user.id,
                  task_assignee__request_status=REQUEST_CHOICES.REJECT) |
                Q(notifier__id=self.request.user.id)).distinct()

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
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class TaskAssigneesList(ListAPIView):
    """
    get:
    Return a list of all the rejected task by current user..
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskAssigneesSerializer
    filterset_fields = ['request_status']

    def get_queryset(self):
        if self.request.user.is_superuser:
            return TaskAssignees.objects.filter()
        return TaskAssignees.objects.filter(assignee_id=self.request.user.id)

    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,)
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = TaskSerializer(self.filter_queryset(queryset), many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class AcceptTask(CreateAPIView):
    """
    Change request_status to accept of the given task.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            task_id = request.data.get('task')
            if not task_id:
                return Response({'task': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)
            task_assignee = TaskAssignees.objects.get(assignee_id=request.user.id, task_id=task_id)
            if task_assignee.request_status != REQUEST_CHOICES.ACCEPT:
                task_assignee.change_request_status(REQUEST_CHOICES.ACCEPT)
                EventLog(description=f"{request.user.username} accepted the task.", task_id=task_id).save()
                return Response({'data': 'Successfully accepted'}, status=status.HTTP_200_OK)
            else:
                return Response({'data': 'Already accepted'}, status=status.HTTP_401_UNAUTHORIZED)
        except TaskAssignees.DoesNotExist:
            return Response({'data': "Not assigned to current user or Task doesn't exist."},
                            status=status.HTTP_400_BAD_REQUEST)


class RejectTask(CreateAPIView):
    """
    Reject the task, assign to user
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            task_id = request.data.get('task')
            reason = request.data.get('reason')
            if task_id and reason:
                task_assignee = TaskAssignees.objects.get(assignee_id=request.user.id, task_id=task_id)
                if task_assignee.request_status != REQUEST_CHOICES.REJECT:
                    task_assignee.change_request_status(REQUEST_CHOICES.REJECT, reason)
                    EventLog(description=f"{request.user.username} rejected task request.", task_id=task_id).save()
                    return Response({'data': 'task is rejected.'}, status=status.HTTP_204_NO_CONTENT)
                else:
                    return Response({'data': 'This task is already rejected by the current user.'},
                                    status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({'task': 'This field is required.', 'reason': 'This field is required.'},
                                status=status.HTTP_400_BAD_REQUEST)
        except TaskAssignees.DoesNotExist:
            return Response({'data': "Not assigned to current user or Task doesn't exist."},
                            status=status.HTTP_400_BAD_REQUEST)


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
        try:
            task = Task.objects.get(id=request.data.get('task'))
            user = User.objects.get(id=request.data.get('user'))
            if task.assignee.id == user.id:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                EventLog(description=f"{request.user.username} commented on the task.", task_id=task.id).save()
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response({'data': 'Current user cannot update this task.'}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'data': 'User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        except Task.DoesNotExist:
            return Response({'data': 'Task does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

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

            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
