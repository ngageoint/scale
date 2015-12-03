from django.contrib import admin
from node.models import Node

class NodeAdmin(admin.ModelAdmin):
    list_display = (u'hostname', u'is_paused', u'is_paused_errors', u'pause_reason', u'last_offer', u'slave_id', u'is_active', u'archived')

admin.site.register(Node, NodeAdmin)
