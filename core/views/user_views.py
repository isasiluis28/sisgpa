# -*- coding: utf-8 -*-
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
    """
    Lista de Usuarios.
    """
    model = User
    context_object_name = 'users'
    template_name = 'core/user/user_list.html'

    def get_queryset(self):
        """
        Retorna una los usuarios excluyendo el AnonymousUse.

        :return:lista de usuarios.
        """
        # todos los udarios menos el anonimo.
        return User.objects.exclude(id=1)

user_list = UserList.as_view()


class UserDetail(LoginRequiredMixin, DetailView):
    """
       Ver detalles de Usuario.
    """
    model = User
    context_object_name = 'usuario'
    template_name = 'core/user/user_detail.html'

    def get_context_data(self, **kwargs):
        """
         Agregar lista de proyectos al contexto.

        :param kwargs: diccionario de argumentos claves.
        :return: contexto.
        """
        context = super(UserDetail, self).get_context_data(**kwargs)
        context['projects'] = self.object.miembroequipo_set.all()
        return context

user_detail = UserDetail.as_view()


class UserCreate(LoginRequiredMixin, CreateViewMixin, CreateView):
    """
        creaccion de usuarios.
    """
    model = User
    form_class = UserCreateForm
    template_name = 'core/user/user_form.html'
    permission_required = 'auth.add_user'

    def get_context_data(self, **kwargs):
        context = super(UserCreate, self).get_context_data(**kwargs)
        context['accion'] = 'agregar'
        return context

    def get_success_url(self):
        """
         Retorna una los usuarios excluyendo el AnonymousUser.

        :return: url del UserDetail.
        """
        return reverse('user_detail', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        """
        Verificar validez del formulario.

        :param form: formulario completado.
        :return: Url de Evento Correcto.
        """
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
    """
        Eliminar un Usuario del Sistema.
    """
    model = User
    template_name = 'core/user/user_delete.html'
    context_object_name = 'usuario'
    success_url = reverse_lazy('user-index')
    permission_required = 'auth.delete_user'

    def delete(self, request, *args, **kwargs):
        """
        Calls the delete() method on the fetched object and then
        redirects to the success URL.

        :param request: HttpRequest.
        :param args: mapear todos los argumentos posicionales a una tupla.
        :param kwargs:mapear todos los argumentos de palabra clave a un diccionario.
        :return:HttpResponse.
        """
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

user_delete = UserDelete.as_view()


class UpdateUser(LoginRequiredMixin, GlobalPermissionMixin, UpdateView):
    """
        Actualizar un usuario del sistema.
    """
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
        """
         Obtener datos iniciales para el formulario.

        :return: url de UserDetail.
        """
        return reverse('user_detail', kwargs={'pk': self.object.id})

    def get_initial(self):
        """
        Obtener datos iniciales para el formulario.

        :return: diccionario con los datos iniciales.
        """
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
        """
         Comprobar validez del formulario recibido.

        :param form: Formulario recibido.
        :return:URL de evento correcto.
        """
        super(UpdateUser, self).form_valid(form)

        # se eliminan permisos anteriores.
        self.object.user_permissions.clear()
        choosed_perms = self.request.POST.getlist('general_perms')
        for perm_codename in choosed_perms:
            perm = Permission.objects.get(codename=perm_codename)
            self.object.user_permissions.add(perm)

        return HttpResponseRedirect(self.get_success_url())

user_update = UpdateUser.as_view()

