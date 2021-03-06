# -*- coding: utf-8 -*-
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models.aggregates import Sum
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.context import RequestContext
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from guardian.shortcuts import get_perms

from core.forms import FlujoCreateForm, ActividadFormSet
from core.models import Flujo, Proyecto
from core.views.views import GlobalPermissionMixin, ActiveProjectRequiredMixin, CreateViewMixin


class FlujoList(LoginRequiredMixin, GlobalPermissionMixin, ListView):
    """
     Vista de los Flujos.
    """
    model = Flujo
    template_name = 'core/flujo/flujo_list.html'
    permission_required = 'core.view_project'
    context_object_name = 'flujos'
    project = None

    def get_permission_object(self):
        if not self.project:
            self.project = get_object_or_404(Proyecto, pk=self.kwargs['project_pk'])
        return self.project

    def get_context_data(self, **kwargs):
        context = super(FlujoList, self).get_context_data(**kwargs)
        context['proyecto_perms'] = get_perms(self.request.user, self.project)
        return context

    def get_queryset(self):
        if not self.project:
            self.project = get_object_or_404(Proyecto, pk=self.kwargs['project_pk'])
        return Flujo.objects.filter(proyecto=self.project)


flujo_list = FlujoList.as_view()


class FlujoDetail(LoginRequiredMixin, GlobalPermissionMixin, DetailView):
    """
     Vista del detalle de los flujos.
    """
    model = Flujo
    template_name = 'core/flujo/flujo_detail.html'
    permission_required = 'core.view_project'
    context_object_name = 'flujo'

    def get_permission_object(self):
        """

        :return: Objeto por el cual comprobar el permiso.
        """
        return self.get_object().proyecto

    def get_context_data(self, **kwargs):
        """
        Agregar lista de actividades al contexto.

        :param kwargs: diccionario de argumentos claves.
        :return: contexto.
        """
        context = super(FlujoDetail, self).get_context_data(**kwargs)
        context['actividades'] = [[a, a.userstory_set.count()] for a in self.object.actividad_set.all()]
        context['act_us'] = [a.userstory_set.order_by('-prioridad') for a in self.object.actividad_set.all()]
        us = self.object.proyecto.userstory_set.filter(actividad__flujo=self.object)  # User Stories del Flujo.
        time = us.aggregate(registrado=Sum('tiempo_registrado'),
                            estimado=Sum('tiempo_estimado'))  # Aggregate retorna None en vez de 0.
        context.update(time)
        return context


flujo_detail = FlujoDetail.as_view()


class AddFlujo(ActiveProjectRequiredMixin, LoginRequiredMixin, CreateViewMixin, CreateView):
    """
     Vista que agrega un flujo al sistema.
    """
    model = Flujo
    template_name = 'core/flujo/flujo_form.html'
    form_class = FlujoCreateForm
    permission_required = 'core.create_flujo'
    proyecto = None

    def get_proyecto(self):
        if not self.proyecto:
            self.proyecto = get_object_or_404(Proyecto, pk=self.kwargs['project_pk'])
        return self.proyecto

    def get_permission_object(self):
        """

        :return:  Objeto por el cual comprobar el permiso.
        """
        if not self.proyecto:
            self.proyecto = get_object_or_404(Proyecto, pk=self.kwargs['project_pk'])
        return self.proyecto

    def get_context_data(self, **kwargs):
        """
         Agregar datos al contexto.


        :param kwargs: argumentos clave.
        :return: contexto.
        """
        context = super(AddFlujo, self).get_context_data(**kwargs)
        context['current_action'] = 'Agregar'
        context['actividad_form'] = ActividadFormSet(self.request.POST if self.request.method == 'POST' else None)
        return context

    def get_success_url(self):
        """

        :return: la url de redireccion a la vista de los detalles del flujo agregado.
        """
        return reverse('flujo_detail', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        """
         Comprobar validez del formulario. Crea una instancia de flujo para asociar con la actividad.

        :param form: formulario recibido.
        :return: URL de redireccion.
        """
        self.object = form.save(commit=False)
        self.object.proyecto = self.get_proyecto()
        self.object.proyecto.estado = 'EP'
        self.object.proyecto.save()
        self.object.save()
        actividad_form = ActividadFormSet(self.request.POST, instance=self.object)
        if actividad_form.is_valid():
            actividad_form.save()
            order = [form.instance.id for form in actividad_form.ordered_forms]
            self.object.set_actividad_order(order)
            return HttpResponseRedirect(self.get_success_url())

        return render(
            self.request, self.get_template_names(),
            {'form': form, 'actividad_form': actividad_form},
            context_instance=RequestContext(self.request)
        )


add_flujo = AddFlujo.as_view()


class UpdateFlujo(ActiveProjectRequiredMixin, LoginRequiredMixin, GlobalPermissionMixin, UpdateView):
    """
    View que actualiza un flujo al sistema.
    """
    model = Flujo
    template_name = 'core/flujo/flujo_form.html'
    form_class = FlujoCreateForm
    permission_required = 'project.edit_flujo'

    def get_proyecto(self):
        return self.get_object().proyecto

    def get_permission_object(self):
        return self.get_object().proyecto

    def get_context_data(self, **kwargs):
        """
        Agregar datos al contexto


        :param kwargs: argumentos clave.
        :return: contexto.
        """
        context = super(UpdateFlujo, self).get_context_data(**kwargs)
        context['current_action'] = "Editar"
        context['actividad_form'] = ActividadFormSet(self.request.POST if self.request.method == 'POST' else None,
                                                     instance=self.object)

        return context

    def get_success_url(self):
        """
        :return:la url de redireccion a la vista de los detalles del flujo agregado.
        """
        return reverse('flujo_detail', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        """
        Comprobar validez del formulario. Crea una instancia de flujo para asociar con la actividad.

        :param form: formulario recibido.
        :param actividad_form: formulario recibido de actividad.
        :return: URL de redireccion.
        """
        self.object = form.save()
        actividad_form = ActividadFormSet(self.request.POST, instance=self.object)
        if actividad_form.is_valid():
            actividad_form.save()
            order = [form.instance.id for form in actividad_form.ordered_forms]
            self.object.set_actividad_order(order)

            return HttpResponseRedirect(self.get_success_url())

        return render(self.request, self.get_template_names(), {'form': form,
                                                                'actividad_form': actividad_form},
                      context_instance=RequestContext(self.request))

flujo_edit = UpdateFlujo.as_view()


class DeleteFlujo(ActiveProjectRequiredMixin, LoginRequiredMixin, GlobalPermissionMixin, DeleteView):
    """
    Vista de Eliminacion de Flujos.
    """
    model = Flujo
    template_name = 'core/flujo/flujo_delete.html'
    permission_required = 'project.delete_flujo'
    context_object_name = 'flujo'

    def get_proyecto(self):
        return self.get_object().proyecto

    def get_permission_object(self):
        return self.get_object().proyecto

    def get_success_url(self):
        return reverse_lazy('flujo_list', kwargs={'project_pk': self.get_object().proyecto.id})


flujo_delete = DeleteFlujo.as_view()