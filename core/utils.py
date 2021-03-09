"""
Task Manager Utils
"""
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from model_utils import Choices

from core.tokens import AccountActivationTokenGenerator

STATUS_CHOICES = Choices('PENDING', 'ACCEPT', 'REJECT')


def send_activation_email(user, request):
    """ send activation link to the user email """
    current_site = get_current_site(request)
    subject = 'Activate Your Task Manager Account'
    message = render_to_string('taskmanager_api/acc_active_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': AccountActivationTokenGenerator().make_token(user),
    })
    send_email(subject, message, [user.email])


def send_email(subject, message, recipient_list, html_message=None, from_email=None):

    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        html_message=html_message,
        fail_silently=False
    )
