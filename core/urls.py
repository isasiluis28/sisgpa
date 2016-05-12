from django.conf.urls import url, include
from core.views import index_view, project_list, project_detail, project_create, project_update, project_delete
from core.views import user_list, user_detail, user_create, user_delete, user_update
from core.views import rol_list, rol_create, rol_detail, rol_update

urlpatterns = [
    url(r'^$', index_view, name='index-view'),
    url(r'^projects/$', project_list, name='projects-index'),
    url(r'^projects/(?P<pk>\d+)/$', project_detail, name='project_detail'),
    url(r'^projects/add/$', project_create, name='project_create'),
    url(r'^projects/(?P<pk>\d+)/edit/$', project_update, name="project_update"),
    url(r'^projects/(?P<pk>\d+)/delete/$', project_delete, name="project_delete"),

    url(r'^users/$', user_list, name='user-index'),
    url(r'^users/(?P<pk>\d+)/$', user_detail, name='user_detail'),
    url(r'^users/add/$', user_create, name='user_create'),
    url(r'^users/(?P<pk>\d+)/delete/$', user_delete, name="user_delete"),
    url(r'^users/(?P<pk>\d+)/edit/$', user_update, name="user_update"),

    url(r'^roles/$', rol_list, name='rol-index'),
    url(r'^roles/add/$', rol_create, name='rol_create'),
    url(r'^roles/(?P<pk>\d+)/$', rol_detail, name='rol_detail'),
    url(r'^roles/(?P<pk>\d+)/edit/$', rol_update, name="rol_update"),

]
