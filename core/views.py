"""
Task Manager Core Views
"""
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from requests import Response
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
    UpdateAPIView
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView

from core.models import User
from core.serializers import (
    ChangePasswordSerializer,
    UserCreateSerializer,
    UserDetailsSerializer,
    UserUpdateSerializer
)
from core.tokens import AccountActivationTokenGenerator


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
    Call to change password.
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

