from __future__ import unicode_literals

from django.contrib import admin
from node.models import Node


class NodeAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'is_paused', 'is_paused_errors', 'pause_reason', 'last_offer', 'slave_id', 'is_active', 'archived')

admin.site.register(Node, NodeAdmin)
