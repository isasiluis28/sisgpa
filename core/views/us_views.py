from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import modelform_factory
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from guardian.mixins import LoginRequiredMixin
from guardian.shortcuts import get_perms
from reversion import revisions as reversion

from core.models import UserStory, Proyecto
from core.views.views import GlobalPermissionMixin, ActiveProjectRequiredMixin, CreateViewMixin


class USList(LoginRequiredMixin, GlobalPermissionMixin, ListView):
    model = UserStory
    template_name = 'core/us/us_list.html'
    permission_required = 'core.view_project'
    context_object_name = 'userstories'
    project = None

    def get_proyecto(self):
        return get_object_or_404(Proyecto, pk=self.kwargs['project_pk'])

    def get_permission_object(self):
        if self.project is None:
            self.project = self.get_proyecto()
        return self.get_proyecto()

    def get_context_data(self, **kwargs):
        context = super(USList, self).get_context_data(**kwargs)
        context['proyecto_perms'] = get_perms(self.request.user, self.get_proyecto())
        return context

    def get_queryset(self):
        return UserStory.objects.filter(proyecto=self.get_proyecto())


us_list = USList.as_view()


class USDetail(LoginRequiredMixin, GlobalPermissionMixin, DetailView):
    model = UserStory
    permission_required = 'core.view_project'
    template_name = 'core/us/us_detail.html'
    context_object_name = 'userstory'

    def get_permission_object(self):
        return self.get_object().proyecto


class AddUserStory(ActiveProjectRequiredMixin, LoginRequiredMixin, CreateViewMixin, CreateView):
    model = UserStory
    template_name = 'core/us/us_form.html'
    permission_required = 'core.create_us'

    def get_context_data(self, **kwargs):
        context = super(AddUserStory, self).get_context_data(**kwargs)
        context['current_action'] = 'Crear'
        return context

    def get_proyecto(self):
        return get_object_or_404(Proyecto, pk=self.kwargs['project_pk'])

    def get_form_class(self):
        project = self.get_proyecto()
        form_fields = ['nombre', 'descripcion', 'valor_negocio', 'valor_tecnico', 'tiempo_estimado']
        if 'prior_us' in get_perms(self.request.user, project):
            form_fields.insert(2, 'prioridad')
        form_class = modelform_factory(UserStory, fields=form_fields)
        return form_class

    def get_permission_object(self):
        return self.get_proyecto()

    def get_success_url(self):
        return reverse('us_detail', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.proyecto = self.get_proyecto()
        self.object.proyecto.estado = 'EP'
        self.object.proyecto.save()

        with transaction.atomic(), reversion.create_revision():
            reversion.set_user(self.request.user)
            reversion.set_comment('Version Inicial')
            self.object.save()

        return HttpResponseRedirect(self.get_success_url())






















