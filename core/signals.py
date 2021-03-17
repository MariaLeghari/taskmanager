from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created
from rest_framework.authtoken.models import Token

from core.utils import send_email


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    create and send reset password token to the user email.
    """
    email_plaintext_message = f"{reverse('password_reset:reset-password-request')}?token={reset_password_token.key}"
    subject = "Password Reset for {title}".format(title="Task Manager"),
    send_email(subject, email_plaintext_message, recipient_list=[reset_password_token.user.email])


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
