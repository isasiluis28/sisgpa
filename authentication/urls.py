from django.conf.urls import url
from django.contrib.auth.views import logout
from authentication.views import login_view

urlpatterns = [
    url(r'^login/$', login_view, name='login-view'),
    url(r'^logout/$', logout, {'next_page': '/login'}, name='logout'),
]
