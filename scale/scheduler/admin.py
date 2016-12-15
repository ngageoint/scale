from __future__ import unicode_literals

from django.contrib import admin
from models import Scheduler


class SchedulerAdmin(admin.ModelAdmin):
    list_display = ('is_paused', 'id')

admin.site.register(Scheduler, SchedulerAdmin)
