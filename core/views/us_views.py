# -*- coding: utf-8 -*-

from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import transaction
from django.forms.models import modelform_factory, modelformset_factory
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from guardian.mixins import LoginRequiredMixin
from guardian.shortcuts import get_perms
from reversion import revisions as reversion
from django.utils import timezone

from core.forms import RegistrarActividadForm
from core.models import UserStory, Proyecto, Actividad, Nota
from core.views.views import GlobalPermissionMixin, ActiveProjectRequiredMixin, CreateViewMixin


class USList(LoginRequiredMixin, GlobalPermissionMixin, ListView):
    """
     Lista de los User Story.
    """
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
    """
        Vista de los detalles de los User Story.
    """
    model = UserStory
    permission_required = 'core.view_project'
    template_name = 'core/us/us_detail.html'
    context_object_name = 'userstory'

    def get_permission_object(self):
        """

        :return: objeto al cual corresponde el permiso.
        """
        return self.get_object().proyecto

us_detail = USDetail.as_view()


class AddUserStory(ActiveProjectRequiredMixin, LoginRequiredMixin, CreateViewMixin, CreateView):
    """
     Vista que agrega un User Story a sistema.
    """
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
        """

        :return: Objeto por el cual comprobar el permiso.
        """
        if not self.proyecto:
            self.proyecto = self.get_proyecto()
        return self.get_proyecto()

    def get_success_url(self):
        """

        :return: la url de redireccion a la vista de los detalles del user story agregado.
        """
        return reverse('us_detail', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        """
         Comprobar Validez del formulario.

        :param form: Dormulario recibido.
        :return: URL de redireccion.
        """
        self.object = form.save(commit=False)
        self.object.proyecto = self.get_proyecto()
        self.object.proyecto.estado = 'EP'
        self.object.proyecto.save()

        with transaction.atomic(), reversion.create_revision():
            reversion.set_user(self.request.user)
            reversion.set_comment('Version Inicial')
            self.object.save()

        return HttpResponseRedirect(self.get_success_url())

add_us = AddUserStory.as_view()


class UpdateUserStory(ActiveProjectRequiredMixin, LoginRequiredMixin, UpdateView):
    """
    View que actualiza un user story del sistema.
    """
    model = UserStory
    template_name = 'core/us/us_form.html'

    def get_proyecto(self):
        return self.get_object().proyecto

    def dispatch(self, request, *args, **kwargs):
        """
        Comprobacion de permisos hecha antes de la llamada al dispatch que inicia el proceso de respuesta al request de la url.

        :param request: request hecho por el cliente.
        :param args: argumentos adicionales posicionales.
        :param kwargs: argumentos adicionales en forma de diccionario.
        :return: PermissionDenied si el usuario no cuenta con permisos.
        """
        if 'edit_us' in get_perms(request.user, self.get_object().proyecto):
            return super(UpdateUserStory, self).dispatch(request, *args, **kwargs)
        elif 'edit_my_us' in get_perms(self.request.user, self.get_object()):
            return super(UpdateUserStory, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied()

    def get_form_class(self):
        project = self.get_object().proyecto
        form_fields = ['nombre', 'descripcion', 'valor_negocio', 'valor_tecnico', 'tiempo_estimado']
        if 'prior_us' in get_perms(self.request.user, project):
            form_fields.insert(2, 'prioridad')
        form_class = modelform_factory(UserStory, fields=form_fields)
        return form_class

    def get_context_data(self, **kwargs):
        """
        Agregar datos al contexto.

        :param kwargs: argumentos clave.
        :return: contexto.
        """
        context = super(UpdateUserStory, self).get_context_data(**kwargs)
        context['current_action'] = "Editar"
        return context

    def get_success_url(self):
        """
        :return:la url de redireccion a la vista de los detalles del user story agregado.
        """
        return reverse('us_detail', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        """
        Comprobar validez del formulario. Crea una instancia de user story.

        :param form: formulario recibido.
        :return: URL de redireccion.
        """
        if form.has_changed():
            with transaction.atomic(), reversion.create_revision():
                self.object = form.save()
                reversion.set_user(self.request.user)
                reversion.set_comment("Modificacion: {}".format(str.join(', ', form.changed_data)))

        return HttpResponseRedirect(self.get_success_url())

update_us = UpdateUserStory.as_view()


class DeleteUserStory(ActiveProjectRequiredMixin, LoginRequiredMixin, GlobalPermissionMixin, DeleteView):
    """
    Vista de Eliminacion de User Stories.
    """
    model = UserStory
    template_name = 'core/us/us_delete.html'
    permission_required = 'project.remove_us'
    context_object_name = 'userstory'

    def get_proyecto(self):
        return self.get_object().proyecto

    def get_permission_object(self):
        return self.get_proyecto()

    def get_success_url(self):
        return reverse_lazy('us_list', kwargs={'project_pk': self.get_object().proyecto.id})


delete_us = DeleteUserStory.as_view()


class RegistrarActividadUserStory(ActiveProjectRequiredMixin, LoginRequiredMixin, generic.UpdateView):
    """
    View que permite registrar los cambios aplicados a un user story
    """
    model = UserStory
    template_name = 'core/us/us_regactivity_form.html'
    error_template = 'core/us/us_error.html'



    def get_proyecto(self):
        return self.get_object().proyecto

    def get_context_data(self, **kwargs):
        context = super(RegistrarActividadUserStory, self).get_context_data(**kwargs)
        return context

    # def dispatch(self, request, *args, **kwargs):
    #     """
    #     Comprobación de permisos hecha antes de la llamada al dispatch que inicia el proceso de respuesta al request de la url
    #     :param request: request hecho por el cliente
    #     :param args: argumentos adicionales posicionales
    #     :param kwargs: argumentos adicionales en forma de diccionario
    #     :return: PermissionDenied si el usuario no cuenta con permisos
    #     """
    #     if 'regactivity_us' in get_perms(request.user, self.get_object().proyecto) \
    #             or ('register_my_us' in get_perms(request.user, self.get_object())): #Comprobacion de permisos
    #         if self.get_object().sprint and self.get_object().sprint.inicio.date() <= timezone.now().date() and self.get_object().sprint.fin.date() >= timezone.now().date():
    #             if self.get_object().actividad:
    #                 current_priority = self.get_object().prioridad
    #                 s = self.get_object().sprint
    #                 a = self.get_object().actividad
    #                 d = self.get_object().desarrollador
    #                 bigger_priorities = UserStory.objects.filter(sprint=s, actividad=a, desarrollador=d, prioridad__gt=current_priority).count()
    #                 if bigger_priorities == 1: #Comprobacion de prioridad del User Story
    #                     if self.get_object().estado == 2: #Comprobacion de estado del User Story
    #                         return super(RegistrarActividadUserStory, self).dispatch(request, *args, **kwargs)
    #                     return render(request, self.error_template, {'userstory': self.get_object(), 'error': "OTRO_ESTADO"})
    #             return render(request, self.error_template, {'userstory': self.get_object(), 'error': "MENOR_PRIORIDAD"})
    #         return render(request, self.error_template, {'userstory': self.get_object(), 'error': "SPRINT_VENCIDO"})
    #     raise PermissionDenied()

    def get_form_class(self):
        """
        Retorna el tipo de formulario que se mostrará en el template. En caso de que
        el usuario cuente con el permiso de editar userstory se le permitirá cambiar la actividad
        del User Story.
        """
        actual_fields = ['estado_actividad']
        if 'edit_us' in get_perms(self.request.user, self.get_object().proyecto) or \
                        'edit_my_us' in get_perms(self.request.user, self.get_object()):
            actual_fields.insert(1, 'actividad')
        return modelform_factory(UserStory, form=RegistrarActividadForm, fields=actual_fields)

    def get_form(self, form_class = None):
        '''
        Personalización del form retornado
        '''

        form = super(RegistrarActividadUserStory, self).get_form(form_class)
        if 'actividad' in form.fields:
            form.fields['actividad'].queryset = Actividad.objects.filter(flujo=self.get_object().actividad.flujo)
        return form

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tiempo_registrado = self.object.tiempo_registrado + form.cleaned_data['horas_a_registrar']
        #nota_form = self.NoteFormset(self.request.POST)
        new_estado = 1
        #movemos el User Story a la sgte actividad en caso de que haya llegado a Done
        if form.cleaned_data['estado_actividad'] == 3:
            new_estado = 1
            try:
                next_actividad = self.object.actividad.get_next_in_order()
            except ObjectDoesNotExist:
                next_actividad = self.object.actividad
                self.object.estado = 3 #Lo marcamos como pendiente de aprobación
                new_estado = 3

            self.object.actividad = next_actividad
            self.object.estado_actividad = new_estado

        self.object.save()

        # if nota_form.is_valid():
        #     for f in nota_form.forms:
        #         n = f.save(commit=False)
        #         n.horas_a_registrar = form.cleaned_data['horas_a_registrar']
        #         n.tiempo_registrado = self.object.tiempo_registrado
        #         n.desarrollador = self.request.user
        #         n.sprint = self.object.sprint
        #         n.actividad = self.object.actividad
        #         n.estado = self.object.estado
        #         n.estado_actividad = self.object.estado_actividad
        #         n.user_story = self.object
        #         n.save()
        #     #self.notify(n)

        return HttpResponseRedirect(self.get_success_url())










