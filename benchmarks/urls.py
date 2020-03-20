from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^by-system/$', views.system_list, name='systems'),
    url(r'^by-system/(?P<name>\w[\w-]*)/$', views.runs_by_system, name='runs-by-system'),
    url(r'^by-task/$', views.model_list, name='models'),
    url(r'^by-task/(?P<model_name>\w[\w-]*)/$', views.model_detail, name='model'),
    url(r'^by-task/(?P<model_name>\w[\w -]*)/(?P<task_name>\w[\w -\/]*)/$', views.measures_by_task, name='measures-by-task'),
    url(r'^runs/$', views.RunListResource.as_view(), name='runs'),
    url(r'^latest/$', views.latest, name='latest'),
    url(r'^documentation/$', views.documentation, name='documentation')
]