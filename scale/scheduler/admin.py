from django.contrib import admin
from models import Scheduler

class SchedulerAdmin(admin.ModelAdmin):
    list_display = (u'is_paused',u'id')

admin.site.register(Scheduler, SchedulerAdmin)
