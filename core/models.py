"""
Task Manager Core Models
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    User Model
    Extra fields in default user model
    """
    email = models.EmailField(unique=True)
    profile_image = models.ImageField(upload_to='profile_pictures/', blank=True)
