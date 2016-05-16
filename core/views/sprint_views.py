import datetime
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.forms.formsets import formset_factory
from django.forms.models import modelform_factory
from django.forms.widgets import SelectDateWidget, HiddenInput
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.context import RequestContext
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from guardian.mixins import LoginRequiredMixin
from guardian.shortcuts import get_perms

from core.forms import SprintCreateBaseForm, AddToSprintForm, AddToSprintFormSet
from core.models import Sprint, Proyecto, Flujo, UserStory
from core.views.views import GlobalPermissionMixin, ActiveProjectRequiredMixin, CreateViewMixin


class SprintList(LoginRequiredMixin, GlobalPermissionMixin, ListView):
    model = Sprint
    template_name = 'core/sprint/sprint_list.html'
    permission_required = 'core.view_project'
    context_object_name = 'sprints'
    project = None

    def get_objeto(self):
        return get_object_or_404(Proyecto, pk=self.kwargs['project_pk'])

    def get_permission_object(self):
        if self.project is None:
            self.project = self.get_objeto()
        return self.get_objeto()

    def get_context_data(self, **kwargs):
        context = super(SprintList, self).get_context_data(**kwargs)
        context['proyecto_perms'] = get_perms(self.request.user, self.get_objeto())
        return context

    def get_queryset(self):
        return Sprint.objects.filter(proyecto=self.get_objeto())

sprint_list = SprintList.as_view()


class SprintDetail(LoginRequiredMixin, GlobalPermissionMixin, DetailView):
    model = Sprint
    permission_required = 'core.view_project'
    template_name = 'core/sprint/sprint_detail.html'
    context_object_name = 'sprint'

    def get_permission_object(self):
        return self.get_object().proyecto

    def get_context_data(self, **kwargs):
        context = super(SprintDetail, self).get_context_data(**kwargs)
        context['userstory_list'] = self.object.userstory_set.order_by('-prioridad')
        return context

sprint_detail = SprintDetail.as_view()


class SprintCreate(ActiveProjectRequiredMixin, LoginRequiredMixin, CreateViewMixin, CreateView):
    model = Sprint
    template_name = 'core/sprint/sprint_form.html'
    permission_required = 'core.create_sprint'
    form_class = modelform_factory(Sprint, form=SprintCreateBaseForm,
                                   widgets={'fecha_inicio': SelectDateWidget, 'proyecto': HiddenInput},
                                   fields={'nombre', 'fecha_inicio', 'proyecto'})
    formset = formset_factory(AddToSprintForm, formset=AddToSprintFormSet, extra=1)
    project = None
    # flujo = None

    def get_proyecto(self):
        return get_object_or_404(Proyecto, pk=self.kwargs['project_pk'])

    # def get_initial(self):
    #     initial = {'project': self.get_proyecto()}
    #     return initial

    def get_permission_object(self):
        if self.project is None:
            self.project = self.get_proyecto()
        return self.get_proyecto()

    def __filtar_formset(self, formset):
        for userformset in formset.forms:
            userformset.fields['desarrollador'].queryset = User.objects.filter(miembroequipo__proyecto=self.get_proyecto())
            userformset.fields['flujo'].queryset = Flujo.objects.filter(proyecto=self.get_proyecto())
            userformset.fields['userstory'].queryset = UserStory.objects.filter(
                Q(proyecto=self.get_proyecto()), Q(estado=2) | Q(estado=1)
            )

    def get_context_data(self, **kwargs):
        """
        agrega el contexto de los formsets formados por desarrolladores, flujos, userstories
        :param kwargs: args extra
        :return: el contexto necesario para los datos
        """
        context = super(SprintCreate, self).get_context_data(**kwargs)
        formset = self.formset(self.request.POST if self.request.method == 'POST' else None)
        self.__filtar_formset(formset)
        context['current_action'] = 'agregar'
        context['formset'] = formset
        return context

    def get_success_url(self):
        """
        :return: la url de redireccion a la vista  de los detalles del sprint agregado
        """
        return reverse('sprint_detail', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        """
        guarda el desarrolador, actividad y sprint asociado al proyecto dentro de un us
        :param form: formulario del sprint
        :return:
        """
        proyecto = self.get_proyecto()
        self.object = form.save(commit=False)
        self.object.fecha_fin = self.object.fecha_inicio + datetime.timedelta(days=self.get_proyecto().duracion_sprint)
        proyecto.estado = 'EP'
        proyecto.save()
        self.object.save()

        formset_b = self.formset(self.request.POST)
        if formset_b.has_changed():
            if formset_b.is_valid():
                for subform in formset_b:
                    new_us = subform.cleaned_data['userstory']
                    new_flujo = subform.cleaned_data['flujo']
                    # self.flujo = new_flujo
                    new_dev = subform.cleaned_data['desarrollador']
                    new_us.desarrolador = new_dev
                    new_us.sprint = self.object
                    new_us.actividad = new_flujo.actividad_set.first()
                    new_us.estado_actividad = 1
                    new_us.estado = 2  # el us pasa a estar en curso por incluirse en el sprint
                    new_us.save()
                return HttpResponseRedirect(self.get_success_url())
            else:
                return render(self.request, self.get_template_names(), {'form': form, 'formset': formset_b,},
                              context_instance=RequestContext(self.request))
        else:
            return HttpResponseRedirect(self.get_success_url())

sprint_create = SprintCreate.as_view()


# class SprintUpdate(ActiveProjectRequiredMixin, LoginRequiredMixin, GlobalPermissionMixin, UpdateView):
#     model = Sprint
#     permission_required = 'core.edit_sprint'
#     template_name = 'core/sprint/sprint_form.html'
#     form_class = modelform_factory(
#         Sprint,
#         form=SprintCreateBaseForm,
#         widgets={'fecha_inicio': SelectDateWidget, 'proyecto': HiddenInput},
#         fields={'nombre', 'fecha_inicio', 'proyecto'}
#     )
#     formset = formset_factory(AddToSprintForm, formset=AddToSprintFormSet, can_delete=True, extra=1)
#     formse
























































