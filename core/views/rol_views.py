from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from guardian.mixins import LoginRequiredMixin
from guardian.shortcuts import remove_perm, get_perms

from core.forms import RolForm
from core.views.views import GlobalPermissionMixin, CreateViewMixin, get_selected_perms


class RolList(LoginRequiredMixin, ListView):
    model = Group
    template_name = 'core/rol/rol_list.html'
    context_object_name = 'roles'

rol_list = RolList.as_view()


class RolDetail(LoginRequiredMixin, DetailView):
    model = Group
    template_name = 'core/rol/rol_detail.html'
    context_object_name = 'rol'

rol_detail = RolDetail.as_view()


class RolCreate(LoginRequiredMixin, CreateViewMixin, CreateView):
    model = Group
    template_name = 'core/rol/rol_form.html'
    form_class = RolForm
    permission_required = 'auth.add_group'

    def get_context_data(self, **kwargs):
        context = super(RolCreate, self).get_context_data(**kwargs)
        context['accion'] = 'agregar'
        return context

    def get_success_url(self):
        return reverse('rol_detail', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        super(RolCreate, self).form_valid(form)
        choosed_perms = get_selected_perms(self.request.POST)
        for perm_codename in choosed_perms:
            perm = Permission.objects.get(codename=perm_codename)
            self.object.permissions.add(perm)
        return HttpResponseRedirect(self.get_success_url())

rol_create = RolCreate.as_view()


class RolUpdate(LoginRequiredMixin, GlobalPermissionMixin, UpdateView):
    model = Group
    template_name = 'core/rol/rol_form.html'
    form_class = RolForm
    permission_required = 'auth.change_group'

    def get_context_data(self, **kwargs):
        context = super(RolUpdate, self).get_context_data(**kwargs)
        context['accion'] = 'editar'
        return context

    def get_success_url(self):
        return reverse('rol_detail', kwargs={'pk': self.object.id})

    def get_initial(self):
        modelo = self.get_object()

        perm_list = [perm.codename for perm in list(modelo.permissions.all())]

        initial = {
            'perms_proyecto': perm_list,
        }
        return initial

    def form_valid(self, form):
        super(RolUpdate, self).form_valid(form)

        # eliminamos permisos anteriores
        self.object.permissions.clear()
        choosed_perms = get_selected_perms(self.request.POST)
        for permname in choosed_perms:
            perm = Permission.objects.get(codename=permname)
            self.object.permissions.add(perm)

        # actualizamos los permisos de los miembros de equipos que tienen este rol
        team_members_set = self.object.miembroequipo_set.all()
        for team_member in team_members_set:
            user = team_member.usuario
            project = team_member.proyecto
            # borramos todos los permisos que tiene asociado el usuario en el proyecto
            for perm in get_perms(user, project):
                # no eliminar el permiso view_project
                if perm != 'view_project':
                    remove_perm(perm, user, project)

            all_roles = team_member.roles.all()
            for role in all_roles:
                # desacociamos al usuario de los demas roles con los que contaba (para que se eliminen los permisos anteriores)
                team_member.roles.remove(role)
                # volvemos a agregar para que se copien los permisos actualizados
                team_member.roles.add(role)
        return HttpResponseRedirect(self.get_success_url())

rol_update = RolUpdate.as_view()