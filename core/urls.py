from django.conf.urls import url, include
from core.views import index_view, project_list

urlpatterns = [
    url(r'^$', index_view, name='index-view'),
    url(r'^projects/$', project_list, name='projects-index'),
]
