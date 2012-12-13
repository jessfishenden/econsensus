from django.db import models
from django.core.urlresolvers import reverse
from datetime import date, datetime

TASK_MANAGERS = (
    ('internal', 'Internal'),
    ('kanban', 'KanbanTool'),   
)

class ActionItem(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    responsible = models.CharField(max_length=100)
    deadline = models.DateField(null=True, blank=True)
    completed_on = models.DateField(null=True, blank=True)
    created_on = models.DateTimeField(default=datetime.now)
    updated_on = models.DateTimeField(null=True, blank=True)
    task_manager = models.CharField(max_length=10, choices=TASK_MANAGERS, default='internal')

    def get_absolute_url(self):
        return reverse('edit_task', kwargs={'pk': self.pk})

    def is_done(self):
        if date.today() >= self.completed_on:
            return True
        return False
    
#class KanbanSetUp(models.Model):
#    api_key = models.CharField(max_length=100)
#    
#class KanbanAction(models.Model):
#    action_item = models.ForeignKey(ActionItem)
#    kanban_id = models.IntegerField()
#    board = models.IntegerField()
#    synced_on = models.DateTimeField()
    
