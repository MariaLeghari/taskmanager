"""
Task Manager API URL Configuration
"""
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from core.views import (
    ActivateAccount,
    ChangePasswordView,
    UserList,
    UserCreateView,
    UserDetailOrUpdateView,
    SendUserActivationEmail
)

urlpatterns = [
    path('list/', UserList.as_view(), name='users'),
    path('current_user/', UserDetailOrUpdateView.as_view(), name='current_user'),
    path('create_user/', UserCreateView.as_view(), name='create_user'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('activate/<uidb64>/<token>', ActivateAccount.as_view(), name='activate_user'),
    path('send_activation_email/', SendUserActivationEmail.as_view(), name='send_activation_email'),
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('obtain-token/', obtain_auth_token, name='login'),
]
