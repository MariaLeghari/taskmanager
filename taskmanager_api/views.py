"""
Task Manager Views
"""
from django.core.mail import send_mail
from django.db.models import Q
from django.dispatch import receiver
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django_filters.rest_framework import DjangoFilterBackend
from django_rest_passwordreset.signals import reset_password_token_created
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListCreateAPIView, ListAPIView, RetrieveUpdateAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status

from taskmanager_api.models import Comment, EventLog, Task, User, RejectedTask
from taskmanager_api.serializers import (
    CommentSerializer,
    ChangePasswordSerializer,
    UserCreateSerializer,
    UserDetailsSerializer,
    UserUpdateSerializer,
    RejectedTaskSerializer,
    TaskSerializer
)
from taskmanager_api.tokens import AccountActivationTokenGenerator


class UserList(ListAPIView):
    """
    Return a list of all the existing users.
    """
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = User.objects.all().order_by('id')
    serializer_class = UserDetailsSerializer


class UserDetailOrUpdateView(RetrieveUpdateAPIView):
    """
    retrieve:
    Return current user details.

    put:
    Update the current user details with new one.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = UserUpdateSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = UserDetailsSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserCreateView(CreateAPIView):
    """
    Create a new user instance.
    """
    permission_classes = (AllowAny,)
    serializer_class = UserCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                user.send_activation_email(request)
                return Response({'data': 'send email'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccount(APIView):
    """
    get:
    Activate the user account.
    """
    permission_classes = (AllowAny,)

    def get(self, request, uidb64, token, *args, **kwargs):
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.filter(pk=uid).first()
        if user:
            if not user.is_active:
                if AccountActivationTokenGenerator().check_token(user, token):
                    user.is_activation_token_used = True
                    user.is_active = True
                    user.save()
                    return Response({'data': 'account is activated.'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'token already used or expired!'}, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                return Response({'data': 'account is already activated.'}, status.HTTP_401_UNAUTHORIZED)

        else:
            return Response({'error': 'user does not exist.'}, status.HTTP_400_BAD_REQUEST)


class SendUserActivationEmail(APIView):
    """
    get:
    Send activation email to the user.
    """
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({'email': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email=email).first()
        if user:
            if not user.is_active:
                user.send_activation_email(request)
                return Response({'data': 'send email'}, status=status.HTTP_200_OK)
            else:
                return Response({'data': 'already activated'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'error': 'user does not exist'}, status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    create and send reset password token to the user email.
    """
    email_plaintext_message = "{}?token={}".format(reverse('password_reset:reset-password-request'),
                                                   reset_password_token.key)

    send_mail(
        # title:
        "Password Reset for {title}".format(title="Some website title"),
        # message:
        email_plaintext_message,
        # from:
        "noreply@somehost.local",
        # to:
        [reset_password_token.user.email]
    )
