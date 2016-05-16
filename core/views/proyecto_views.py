from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelform_factory, inlineformset_factory
from django.forms.widgets import SelectDateWidget, CheckboxSelectMultiple
from django.template.context import RequestContext
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from guardian.shortcuts import get_perms, remove_perm

from core.models import Proyecto, MiembroEquipo
from core.views.views import GlobalPermissionMixin, CreateViewMixin, ActiveProjectRequiredMixin


class ProjectList(LoginRequiredMixin, ListView):
    # listado de los proyectos de acuerdo a los permisos de usuario autenticado
    model = Proyecto
    context_object_name = 'projects'
    template_name = 'core/projects/project_list.html'

    def get_queryset(self):
        if self.request.user.has_perm('core.list_all_projects'):
            proyectos = Proyecto.objects.all()
        else:
            proyectos = self.request.user.proyecto_set
        return proyectos.exclude(estado='CA')

project_list = ProjectList.as_view()


class ProjectDetail(LoginRequiredMixin, GlobalPermissionMixin, DetailView):
    model = Proyecto
    context_object_name = 'project'
    permission_required = 'core.view_project'
    template_name = 'core/projects/project_detail.html'

    def get_context_data(self, **kwargs):
        context = super(ProjectDetail, self).get_context_data(**kwargs)
        context['equipo'] = self.object.miembroequipo_set.all()
        context['sprints'] = self.object.sprint_set.all()
        context['flujos'] = self.object.flujo_set.all()
        return context

project_detail = ProjectDetail.as_view()


class ProjectCreate(LoginRequiredMixin, CreateViewMixin, CreateView):
    model = Proyecto
    permission_required = 'core.add_proyecto'
    success_url = reverse_lazy('projects-index')
    form_class = modelform_factory(
        Proyecto,
        widgets={'fecha_inicio': SelectDateWidget, 'fecha_fin': SelectDateWidget},
        fields=('nombre_corto', 'nombre_largo', 'fecha_inicio', 'fecha_fin', 'descripcion')
    )
    template_name = 'core/projects/project_form.html'
    TeamMemberInlineFormSet = inlineformset_factory(Proyecto, MiembroEquipo, can_delete=True,
                                                    fields=['usuario', 'roles'],
                                                    extra=1,
                                                    widgets={'roles': CheckboxSelectMultiple}
                                                    )

    def get_context_data(self, **kwargs):
        context = super(ProjectCreate, self).get_context_data(**kwargs)
        context['formset'] = self.TeamMemberInlineFormSet(self.request.POST if self.request.method == 'POST' else None)
        return context

    def form_valid(self, form):
        # guarda los miembros del equipo asignandolos al respectivo proyecto
        self.object = form.save()
        formset = self.TeamMemberInlineFormSet(self.request.POST, instance=self.object)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(self.get_success_url())

        return render(self.request, self.get_template_names(), {'form': form, 'formset': formset},
                      context_instance=RequestContext(self.request))

project_create = ProjectCreate.as_view()


class ProjectUpdate(ActiveProjectRequiredMixin, LoginRequiredMixin, GlobalPermissionMixin, UpdateView):
    model = Proyecto
    permission_required = 'project.change_proyecto'
    template_name = 'core/projects/project_form.html'
    TeamMemberInlineFormSet = inlineformset_factory(Proyecto, MiembroEquipo, can_delete=True,
                                                    fields=['usuario', 'roles'],
                                                    extra=1,
                                                    widgets={'roles': CheckboxSelectMultiple})
    form_class = modelform_factory(Proyecto,
                                   widgets={'inicio': SelectDateWidget, 'fin': SelectDateWidget},
                                   fields=('nombre_corto', 'nombre_largo', 'fecha_inicio', 'fecha_fin',
                                           'descripcion'),
                                   )

    def get_proyecto(self):
        return self.get_object()

    def form_valid(self, form):
        self.object = form.save()
        formset = self.TeamMemberInlineFormSet(self.request.POST, instance=self.object)
        if formset.is_valid():
            # borramos todos los permisos asociados al usuario en el proyecto antes de volver a asignar los nuevos
            project = self.object
            for form in formset:
                if form.has_changed():  #solo los formularios con cambios efectuados
                    user = form.cleaned_data['usuario']
                    #si se cambia el usuario, borrar permisos del usuario anterior
                    if 'usuario' in form.changed_data and 'usuario' in form.initial:
                        original_user = get_object_or_404(User, pk=form.initial['usuario'])
                        for perm in get_perms(original_user, project):
                            remove_perm(perm, original_user, project)
                    else:
                        for perm in get_perms(user, project):
                            remove_perm(perm, user, project)

            formset.save()
            return HttpResponseRedirect(self.get_success_url())

        return render(self.request, self.get_template_names(), {'form': form, 'formset': formset},
                      context_instance=RequestContext(self.request))

    def get_context_data(self, **kwargs):
        context = super(ProjectUpdate, self).get_context_data(**kwargs)
        context['accion'] = 'editar'
        context['formset'] = self.TeamMemberInlineFormSet(self.request.POST if self.request.method == 'POST' else None, instance=self.object)
        return context

project_update = ProjectUpdate.as_view()


class ProjectDelete(ActiveProjectRequiredMixin, LoginRequiredMixin, GlobalPermissionMixin, DeleteView):
    model = Proyecto
    template_name = 'core/projects/project_delete.html'
    success_url = reverse_lazy('projects-index')
    permission_required = 'project.delete_proyecto'

    def get_proyecto(self):
        return self.get_object()

    def delete(self, request, *args, **kwargs):
        """
        Llama al metodo delete() del objeto
        y luego redirige a la url exitosa.
        """
        self.object = self.get_object()
        success_url = self.get_success_url()
        if False:
            self.object.delete()
        else:
            self.object.estado = 'CA'
            self.object.save(update_fields=['estado'])
        return HttpResponseRedirect(success_url)

project_delete = ProjectDelete.as_view()