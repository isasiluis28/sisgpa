# -*- coding: utf-8 -*-
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

from core.forms import SprintCreateBaseForm, AddToSprintForm, AddToSprintFormset
from core.models import Sprint, Proyecto, Flujo, UserStory
from core.views.views import GlobalPermissionMixin, ActiveProjectRequiredMixin, CreateViewMixin


class SprintList(LoginRequiredMixin, GlobalPermissionMixin, ListView):
    """

      Vista de Listado de Sprint en el sistema.
    """
    model = Sprint
    template_name = 'core/sprint/sprint_list.html'
    permission_required = 'core.view_project'
    context_object_name = 'sprints'
    project = None

    def get_objeto(self):
        return get_object_or_404(Proyecto, pk=self.kwargs['project_pk'])

    def get_permission_object(self):
        """
         Obtener el permiso de un objeto.

        :return: retorna el objeto proyecto donde se comprueba el permiso.
        """
        if self.project is None:
            self.project = self.get_objeto()
        return self.get_objeto()

    def get_context_data(self, **kwargs):
        """
         Agregar datos al contexto.

        :param kwargs:argumentos clave.
        :return:  retorna el contexto.
        """
        context = super(SprintList, self).get_context_data(**kwargs)
        context['proyecto_perms'] = get_perms(self.request.user, self.get_objeto())
        return context

    def get_queryset(self):
        """
        obtiene el projecto correspondiente al seleccionado previamente.

        :return: Los objetos Spritn del proyecto previamente seleccionado.
        """
        return Sprint.objects.filter(proyecto=self.get_objeto())


sprint_list = SprintList.as_view()


class SprintDetail(LoginRequiredMixin, GlobalPermissionMixin, DetailView):
    """
     Vista del detalle de un Sprint en el sistema.
    """
    model = Sprint
    permission_required = 'core.view_project'
    template_name = 'core/sprint/sprint_detail.html'
    context_object_name = 'sprint'

    def get_permission_object(self):
        """
        Obtener el permiso de un objeto.

        :return: retorna el objeto proyecto donde se comprueba el permiso.
        """
        return self.get_object().proyecto

    def get_context_data(self, **kwargs):
        """
         Agregar datos al context.

        :param kwargs:argumentos clave.
        :return:  retorna el contexto.
        """
        context = super(SprintDetail, self).get_context_data(**kwargs)
        context['userstory_list'] = self.object.userstory_set.order_by('-prioridad')
        return context


sprint_detail = SprintDetail.as_view()


class SprintCreate(ActiveProjectRequiredMixin, LoginRequiredMixin, CreateViewMixin, CreateView):
    """
    Vista para agregar un Sprint en el sistema y añadir este sprint, un desarrollador y una actividad al user Story
    """
    # TODO Mostrar como initial data del formset los US que quedaron del sprint anterior
    model = Sprint
    template_name = 'core/sprint/sprint_form.html'
    permission_required = 'project.create_sprint'
    form_class = modelform_factory(Sprint, form=SprintCreateBaseForm,
                                   widgets={'fecha_inicio': SelectDateWidget, 'proyecto': HiddenInput},
                                   fields={'nombre', 'fecha_inicio', 'proyecto'})
    formset = formset_factory(AddToSprintForm, formset=AddToSprintFormset, extra=1)

    proyecto = None

    def get_proyecto(self):
        return get_object_or_404(Proyecto, id=self.kwargs['project_pk'])

    def get_initial(self):
        """
        Datos iniciales para el formulario
        :return: diccionario de datos
        """
        initial = {'proyecto': self.get_proyecto()}
        return initial

    def get_permission_object(self):
        """
        Obtener el permiso de un objeto
        :param: self
        :return: retorna el objeto proyecto donde se comprueba el permiso
        """
        return get_object_or_404(Proyecto, id=self.kwargs['project_pk'])

    def get_success_url(self):
        """
        :return:la url de redireccion a la vista de los detalles del sprint agregado.
        """
        return reverse('sprint_detail', kwargs={'pk': self.object.id})

    def __filtrar_formset__(self, formset):
        for userformset in formset.forms:
            userformset.fields['desarrollador'].queryset = User.objects.filter(miembroequipo__proyecto=self.proyecto)
            userformset.fields['flujo'].queryset = Flujo.objects.filter(proyecto=self.proyecto)
            userformset.fields['userstory'].queryset = UserStory.objects.filter(Q(proyecto=self.proyecto),
                                                                                Q(estado=1) | Q(estado=0))

    def get_context_data(self, **kwargs):
        """
        Agregar datos al contexto como los desarrolladores del projecto, el flujo y los userStory
        :param:**kwargs : argumentos clave
        :return: retorna el contexto
        """
        context = super(SprintCreate, self).get_context_data(**kwargs)
        self.proyecto = self.get_proyecto()
        formset = self.formset(self.request.POST if self.request.method == 'POST' else None)
        self.__filtrar_formset__(formset)
        context['current_action'] = 'Agregar'
        context['formset'] = formset
        return context

    def form_valid(self, form):
        """
        Guarda el desarrollador, actividad y sprint asociado al un projecto dentro de un User Story
        :param form: formulario del sprint
        :return: vuelve a la pagina de detalle del sprint o renderea la pagina marcando los errores para volver a enviar sin errores
        """

        self.proyecto = self.get_proyecto()
        self.object = form.save(commit=False)
        self.object.fecha_fin = self.object.fecha_inicio + datetime.timedelta(days=self.proyecto.duracion_sprint)
        self.proyecto.estado = 'EP'
        self.proyecto.save()
        self.object.save()
        formsetb = self.formset(self.request.POST)
        if formsetb.has_changed():
            if formsetb.is_valid():
                for subform in formsetb:
                    new_userStory = subform.cleaned_data['userstory']
                    new_flujo = subform.cleaned_data['flujo']
                    self.flujo = new_flujo
                    new_desarrollador = subform.cleaned_data['desarrollador']
                    new_userStory.desarrolador = new_desarrollador
                    new_userStory.sprint = self.object
                    new_userStory.actividad = self.flujo.actividad_set.first()
                    new_userStory.estado_actividad = 1
                    new_userStory.estado = 2  # El User Story pasa a estar en curso por incluirse en el Sprint
                    new_userStory.save()
                return HttpResponseRedirect(self.get_success_url())
            else:
                return render(self.request, self.get_template_names(), {'form': form, 'formset': formsetb},
                              context_instance=RequestContext(self.request))
        else:
            return HttpResponseRedirect(self.get_success_url())


sprint_create = SprintCreate.as_view()


class UpdateSprintView(ActiveProjectRequiredMixin, LoginRequiredMixin, GlobalPermissionMixin,
                       UpdateView):
    """
    Vista para actualizar los datos del Sprint y  del UserStory que son el desarrollador, la actividad y el Sprint.
    """
    model = Sprint
    permission_required = 'project.edit_sprint'
    template_name = 'core/sprint/sprint_form.html'
    form_class = modelform_factory(Sprint, form=SprintCreateBaseForm,
                                   widgets={'fecha_inicio': SelectDateWidget, 'proyecto': HiddenInput},
                                   fields={'nombre', 'fecha_inicio', 'proyecto'})
    UserStoryFormset = formset_factory(AddToSprintForm, formset=AddToSprintFormset, can_delete=True, extra=1)
    formset = None

    def get_proyecto(self):
        return self.get_object().proyecto

    def get_permission_object(self):
        """
         permiso para add, edit o delete

        :return: los permisos.
        """
        return self.get_object().proyecto

    def get_success_url(self):
        """
        :return:la url de redireccion a la vista de los detalles del sprint modificado.
        """
        return reverse('sprint_detail', kwargs={'pk': self.object.id})

    def __filtrar_formset__(self, formset):
        for userformset in formset.forms:
            userformset.fields['desarrollador'].queryset = User.objects.filter(
                miembroequipo__proyecto=self.object.proyecto)
            userformset.fields['flujo'].queryset = Flujo.objects.filter(proyecto=self.object.proyecto)
            userformset.fields['userstory'].queryset = UserStory.objects.filter(proyecto=self.object.proyecto)

    def get_context_data(self, **kwargs):
        """
        Especifica los datos de contexto a pasar al template,

        :param kwargs: Diccionario con parametros con nombres clave.
        :return: los datos de contexto.
        """
        context = super(UpdateSprintView, self).get_context_data(**kwargs)
        current_us = self.get_object().userstory_set.all()
        formset = self.UserStoryFormset(self.request.POST if self.request.method == 'POST' else None, initial=[
            {'userstory': us, 'flujo': us.actividad.flujo, 'desarrollador': us.desarrolador} for us in current_us])
        self.__filtrar_formset__(formset)
        context['current_action'] = 'Editar'
        context['formset'] = formset
        return context

    def form_valid(self, form):
        """
        Guarda el desarrollador, actividad y sprint asociado al un projecto dentro de un User Story.

        :param form: formulario del sprint.
        :return: vuelve a la pagina de detalle del sprint.
        """
        self.object = form.save(commit=False)
        self.object.fecha_fin = self.object.fecha_inicio + datetime.timedelta(days=self.object.proyecto.duracion_sprint)
        self.object.save()
        formsetb = self.UserStoryFormset(self.request.POST)
        if formsetb.is_valid():
            proccessed_forms = []
            for subform in formsetb:
                if subform.has_changed() and 'userstory' in subform.cleaned_data:
                    new_userStory = subform.cleaned_data['userstory']
                    if subform in formsetb.deleted_forms and not new_userStory in proccessed_forms:
                        # desaciamos los user story que se eliminaron del form.
                        new_userStory.desarrollador = None
                        new_userStory.sprint = None
                        new_userStory.actividad = None
                    else:
                        new_flujo = subform.cleaned_data['flujo']
                        self.flujo = new_flujo
                        new_desarrollador = subform.cleaned_data['desarrollador']
                        if new_userStory.estado != 5 and new_userStory.estado != 4:  # si el user story no ha finalizado.
                            new_userStory.desarrolador = new_desarrollador
                            new_userStory.sprint = self.object
                            new_userStory.actividad = self.flujo.actividad_set.first()
                            new_userStory.estado = 2
                            new_userStory.estado_actividad = 2
                    new_userStory.save()
                    proccessed_forms.append(new_userStory)
            return HttpResponseRedirect(self.get_success_url())

        self.__filtrar_formset__(formsetb)
        return render(self.request, self.get_template_names(), {'form': form, 'formset': formsetb},
                      context_instance=RequestContext(self.request))


sprint_update = UpdateSprintView.as_view()
