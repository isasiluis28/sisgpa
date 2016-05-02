from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelform_factory, inlineformset_factory
from django.forms.widgets import SelectDateWidget, CheckboxSelectMultiple
from django.template.context import RequestContext
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.http.response import HttpResponseRedirect
from django.shortcuts import render

from core.models import Proyecto, MiembroEquipo
from core.views.views import GlobalPermissionMixin, CreateViewMixin


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