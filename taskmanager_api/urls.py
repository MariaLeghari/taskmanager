"""
Task Manager API URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from taskmanager_api.views import (
    ActivateAccount,
    AcceptTask,
    CommentViewSet,
    ChangePasswordView,
    UserCreateView,
    UserDetailOrUpdateView,
    UserList,
    RejectTask,
    SendUserActivationEmail,
    TaskViewSet
)

router = DefaultRouter()
router.register('tasks', TaskViewSet, basename='tasks')
router.register('comments', CommentViewSet, basename='comments')

urlpatterns = [
    path('users/', UserList.as_view(), name='users'),
    path('current_user/', UserDetailOrUpdateView.as_view(), name='current_user'),
    path('create_user/', UserCreateView.as_view(), name='create_user'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('activate/<uidb64>/<token>', ActivateAccount.as_view(), name='activate_user'),
    path('send_activation_email/', SendUserActivationEmail.as_view(), name='send_activation_email'),
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),

    path('reject_task/', RejectTask.as_view(), name='reject_task'),
    path('accept_task/', AcceptTask.as_view(), name='accept_task'),
]

urlpatterns += router.urls
