""" Task Manager Admin"""
from django.contrib import admin
from django.contrib.admin.utils import flatten_fieldsets
from django.contrib.auth.admin import UserAdmin

from taskmanager_api.models import Comment, EventLog, User, RejectedTask, Task

UserAdmin.fieldsets += (
    ('Other Information',
     {'fields': ('profile_image',)}
     ),
)


class TaskAdmin(admin.ModelAdmin):
    """ Task Admin View """
    list_display = ('title', 'request_status')
    filter_horizontal = ('notifier',)

    def formfield_for_dbfield(self, *args, **kwargs):
        formfield = super().formfield_for_dbfield(*args, **kwargs)
        if formfield:
            formfield.widget.can_delete_related = False
        return formfield


admin.site.register(Comment)
admin.site.register(EventLog)
admin.site.register(User, UserAdmin)
admin.site.register(RejectedTask)
admin.site.register(Task, TaskAdmin)
