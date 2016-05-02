from django.conf.urls import url, include
from core.views import index_view, project_list, project_detail, project_create
from core.views.user_views import user_list, user_detail

urlpatterns = [
    url(r'^$', index_view, name='index-view'),
    url(r'^projects/$', project_list, name='projects-index'),
    url(r'^projects/(?P<pk>\d+)/$', project_detail, name='project_detail'),
    url(r'^projects/add/$', project_create, name='project_create'),

    url(r'^users/$', user_list, name='user-index'),
    url(r'^users/(?P<pk>\d+)/$', user_detail, name='user_detail'),
]
