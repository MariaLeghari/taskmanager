"""
Task Manager Core Serializers
"""
from rest_framework import serializers

from core.models import User


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
    password = serializers.CharField(style={'input_type': 'password'}, min_length=8, max_length=14, write_only=True,
                                     required=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
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
