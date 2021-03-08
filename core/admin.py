"""
Task Manager Core Admin
"""
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin

from core.models import User

UserAdmin.fieldsets += (
    ('Other Information',
     {'fields': ('profile_image',)}
     ),
)

admin.site.register(User, UserAdmin)
