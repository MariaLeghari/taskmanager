"""
Task Manager Core Models
"""
from django.contrib.auth.models import AbstractUser
from django.contrib.sites.shortcuts import get_current_site
from django.db import models
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode

from core.tokens import AccountActivationTokenGenerator


class User(AbstractUser):
    """
    User Model
    Extra fields in default user model
    """
    email = models.EmailField(unique=True)
    profile_image = models.ImageField(upload_to='profile_pictures/', blank=True)

    def send_activation_email(self, request):
        """ send activation link to the user email """
        current_site = get_current_site(request)
        subject = 'Activate Your Task Manager Account'
        from django.utils.encoding import force_bytes
        message = render_to_string('taskmanager_api/acc_active_email.html', {
            'user': self,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(self.pk)),
            'token': AccountActivationTokenGenerator().make_token(self),
        })
        self.email_user(subject, message)
