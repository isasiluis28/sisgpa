from django.contrib.auth.models import User
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from guardian.mixins import LoginRequiredMixin


class UserList(LoginRequiredMixin, ListView):
    model = User
    context_object_name = 'users'
    template_name = 'core/user/user_list.html'

    def get_queryset(self):
        # todos los udarios menos el anonimo
        return User.objects.exclude(id=1)

user_list = UserList.as_view()


class UserDetail(LoginRequiredMixin, DetailView):
    model = User
    context_object_name = 'usuario'
    template_name = 'core/user/user_detail.html'

    def get_context_data(self, **kwargs):
        context = super(UserDetail, self).get_context_data(**kwargs)
        context['projects'] = self.object.miembroequipo_set.all()
        return context

user_detail = UserDetail.as_view()
