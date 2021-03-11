""" Task Manager Admin"""
from django.contrib import admin

from taskmanager_api.models import Comment, EventLog, Task, TaskAssignees


class TaskAssigneeInLine(admin.TabularInline):
    model = TaskAssignees
    extra = 1


class TaskAdmin(admin.ModelAdmin):
    """ Task Admin View """
    list_display = ('title', 'task_status')
    filter_horizontal = ('notifier',)
    inlines = [TaskAssigneeInLine]

    def formfield_for_dbfield(self, *args, **kwargs):
        formfield = super().formfield_for_dbfield(*args, **kwargs)
        if formfield:
            formfield.widget.can_delete_related = False
        return formfield


admin.site.register(Comment)
admin.site.register(EventLog)
admin.site.register(TaskAssignees)
admin.site.register(Task, TaskAdmin)
