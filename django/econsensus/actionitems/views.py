from django.core.urlresolvers import reverse_lazy
from django.views.generic import ListView
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView
from datetime import date

from models import ActionItem
from forms import ActionItemCreateForm, ActionItemUpdateForm

class ActionItemList(ListView):
    model = ActionItem
    template_name = 'actionitems/list.html'
    context_object_name = 'task_list'

class ActionItemCreate(CreateView):
    model = ActionItem
    template_name = 'actionitems/create.html'
    success_url = reverse_lazy('list_tasks')
    form_class = ActionItemCreateForm

class ActionItemUpdate(UpdateView):
    model = ActionItem
    template_name = 'actionitems/edit.html'
    form_class = ActionItemUpdateForm
    
    def post(self, request, *args, **kwargs):
        task = ActionItem.objects.get(pk=kwargs.get('pk'))
        self.handle_done(request, task)
        return super(ActionItemUpdate, self).post(request, *args, **kwargs)
    
    def handle_done(self, request, task):
        f = ActionItemUpdateForm(request.POST, instance=task)
        task = f.save(commit=False)
        if not task.completed_on and 'done' in request.POST:
            task.completed_on = date.today()
        if task.completed_on and not 'done' in request.POST:
            task.completed_on = None
        task.save()

class ActionItemSync(UpdateView):
    
    def get(self, request, *args, **kwargs):
        updateview = ActionItem.objects.get(pk=kwargs.get('pk'))
        task = ActionItem.objects.get(pk=kwargs.get('pk'))
        self.synctask(task)
        return redirect(updateview)
        
    def synctask(self, task):
        f = ActionItemUpdateForm(instance=task)
        task = f.save(commit=False)
        # In the future this will pull in data from external task manager
        task.description += ' sync' 
        task.save()
