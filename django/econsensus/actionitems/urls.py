from django.conf.urls import patterns, include, url
from views import ActionItemList, ActionItemCreate, ActionItemUpdate, ActionItemSync

urlpatterns = patterns('',
    url(r'^$', ActionItemList.as_view(), name='list_tasks'),
    url(r'add/$', ActionItemCreate.as_view(), name='add_task'),
    url(r'(?P<pk>[\d]+)/$', ActionItemUpdate.as_view(), name='edit_task'),
    url(r'(?P<pk>[\d]+)/sync/$', ActionItemSync.as_view(), name='sync_task'),
)
