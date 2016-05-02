from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse, reverse_lazy
from django.forms.models import modelform_factory
from django.http.response import HttpResponseRedirect
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from guardian.mixins import LoginRequiredMixin

from core.forms import UserCreateForm, UserEditForm
from core.views.views import CreateViewMixin, GlobalPermissionMixin


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


class UserCreate(LoginRequiredMixin, CreateViewMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = 'core/user/user_form.html'
    permission_required = 'auth.add_user'

    def get_context_data(self, **kwargs):
        context = super(UserCreate, self).get_context_data(**kwargs)
        context['accion'] = 'agregar'
        return context

    def get_success_url(self):
        return reverse('user_detail', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        super(UserCreate, self).form_valid(form)
        print self.request.POST
        # se agregan los permisos puestos al current usuario.
        choosed_perms = self.request.POST.getlist('general_perms')
        for perm_codename in choosed_perms:
            perm = Permission.objects.get(codename=perm_codename)
            self.object.user_permissions.add(perm)
        return HttpResponseRedirect(self.get_success_url())

user_create = UserCreate.as_view()


class UserDelete(LoginRequiredMixin, GlobalPermissionMixin, DeleteView):
    model = User
    template_name = 'core/user/user_delete.html'
    context_object_name = 'usuario'
    success_url = reverse_lazy('user-index')
    permission_required = 'auth.delete_user'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

user_delete = UserDelete.as_view()


class UpdateUser(LoginRequiredMixin, GlobalPermissionMixin, UpdateView):
    model = User
    template_name = 'core/user/user_form.html'
    permission_required = 'auth.change_user'
    form_class = modelform_factory(
        User,
        form=UserEditForm,
        fields=('first_name', 'last_name', 'email', 'username', 'is_active')
    )

    def get_context_data(self, **kwargs):
        context = super(UpdateUser, self).get_context_data(**kwargs)
        context['accion'] = 'editar'
        return context

    def get_success_url(self):
        return reverse('user_detail', kwargs={'pk': self.object.id})

    def get_initial(self):
        modelo = self.get_object()
        first_name = self.object.first_name
        last_name = self.object.last_name
        email = self.object.email
        username = self.object.username
        password = self.object.password
        perm_list = [perm.codename for perm in list(modelo.user_permissions.all())]

        initial = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'username': username,
            'general_perms': perm_list,
            'password': password
        }

        return initial

    def form_valid(self, form):
        super(UpdateUser, self).form_valid(form)

        # se eliminan permisos anteriores
        self.object.user_permissions.clear()
        choosed_perms = self.request.POST.getlist('general_perms')
        for perm_codename in choosed_perms:
            perm = Permission.objects.get(codename=perm_codename)
            self.object.user_permissions.add(perm)

        return HttpResponseRedirect(self.get_success_url())

user_update = UpdateUser.as_view()







