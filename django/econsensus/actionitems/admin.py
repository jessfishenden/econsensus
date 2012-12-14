from models import ActionItem
from django.contrib import admin

class ActionItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'initiator', 'title', 'responsible', 'deadline', 'is_done')

admin.site.register(ActionItem, ActionItemAdmin)
