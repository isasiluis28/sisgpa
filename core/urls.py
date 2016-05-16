from django.conf.urls import url, include
from core.views import index_view, project_list, project_detail, project_create, project_update, project_delete
from core.views import user_list, user_detail, user_create, user_delete, user_update
from core.views import rol_list, rol_create, rol_detail, rol_update
from core.views.fujo_views import flujo_list, flujo_detail
from core.views.sprint_views import sprint_list, sprint_create, sprint_detail
from core.views.us_views import us_list, us_detail

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

    url(r'^projects/(?P<project_pk>\d+)/sprint/$', sprint_list, name="sprint_list"),
    url(r'^projects/(?P<project_pk>\d+)/sprint/add/$', sprint_create, name="sprint_create"),
    url(r'^sprint/(?P<pk>\d+)/$', sprint_detail, name='sprint_detail'),

    url(r'^projects/(?P<project_pk>\d+)/userstories/$', us_list, name="us_list"),
    url(r'^userstory/(?P<pk>\d+)/$', us_detail, name='us_detail'),

    url(r'^projects/(?P<project_pk>\d+)/flujo/$', flujo_list, name="flujo_list"),
    url(r'^flujo/(?P<pk>\d+)/$', flujo_detail, name='flujo_detail'),

]
