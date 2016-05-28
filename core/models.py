# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy
from django.db import models
from django.utils import timezone
from django.db.models import Sum
from django.db.models.signals import m2m_changed
from django.shortcuts import get_object_or_404
from guardian.shortcuts import assign_perm, remove_perm, get_perms, get_perms_for_model
from reversion import revisions as reversion


class Proyecto(models.Model):
    """
    Modelo de Proyecto del sistema
    """
    ESTADOS = (
        ('EP', 'En Produccion'),
        ('CO', 'Completado'),
        ('AP', 'Aprobado'),
        ('CA', 'Cancelado'),
        ('IN', 'Inactivo')
    )

    nombre_corto = models.CharField(max_length=20)
    nombre_largo = models.CharField(max_length=40)
    estado = models.CharField(max_length=2, choices=ESTADOS, default='IN')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    duracion_sprint = models.PositiveIntegerField(default=30) # en dias
    descripcion = models.TextField()
    equipo = models.ManyToManyField(User, through='MiembroEquipo')

    class Meta:
        # Los permisos estaran asociados a los proyectos, por lo que todos los permisos de ABM de las entidades
        # dependientes del proyecto, deben crearse como permisos de proyecto
        # en vez de 'add', 'change' y 'delete', los permisos personalizados seran 'create', 'edit' y 'remove' para
        # evitar confusiones con los por defecto.

        permissions = (
            ('list_all_projects', 'listar los proyectos disponibles'),
            ('view_project', 'ver el proyecto'),
            ('aprove_project', 'aprobar el proyecto'),

            ('create_sprint', 'agregar sprint'),
            ('edit_sprint', 'editar sprint'),
            ('remove_sprint', 'eliminar sprint'),

            ('create_flujo', 'agregar flujo'),
            ('edit_flujo', 'editar flujo'),
            ('remove_flujo', 'eliminar flujo'),

            ('create_us', 'agregar user story'),
            ('edit_us', 'editar user story'),
            ('remove_us', 'eliminar user story'),
            ('prior_us', 'asignar prioridad a user story'),
            ('regactivity_us', 'registrar avances en user stories'),
            ('aprove_us', 'aprobar user stories completados'),
            ('cancel_us', 'cancelar user stories completados'),
        )

    def __unicode__(self):
        return self.nombre_corto

    def get_absolute_url(self):
        return reverse_lazy('project_detail', args=[self.pk])

    def get_horas_estimadas(self):
        return self.userstory_set.aggregate(total=Sum('tiempo_estimado'))['total']

    def get_horas_trabajadas(self):
        return self.userstory_set.aggregate(total=Sum('tiempo_registrado'))['total']

    def _get_progreso(self):
        us_total = self.userstory_set.count() - self.userstory_set.filter(estado=5).count()
        us_aprobados = self.userstory_set.filter(estado=4).count()
        progreso = float(us_aprobados) / us_total * 100 if us_total > 0 else 0
        return int(progreso)
    progreso = property(_get_progreso)

    def clean(self):
        try:
            if self.fecha_inicio > self.fecha_fin:
                raise ValidationError(
                    {'fecha_inicio': 'Fecha de inicio no puede ser mayor a la fecha de fin.'}
                )
        except TypeError:
            # si se trata de una fecha nula, el propio clean del field se encarga de validar.
            pass


class MiembroEquipo(models.Model):
    """
        Miembros del equipo de un proyecto con un rol específico.
    """
    proyecto = models.ForeignKey(Proyecto)
    usuario = models.ForeignKey(User)
    roles = models.ManyToManyField(Group)

    class Meta:
        default_permissions = ()
        verbose_name = 'Miembros del Equipo'
        unique_together = ('usuario', 'proyecto')
    
    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super(MiembroEquipo, self).save(force_insert, force_update, using, update_fields)
        # se agrega el permiso de view_project al usuario dentro del proyecto hecho.
        assign_perm('view_project', self.usuario, self.proyecto)

    def delete(self, using=None, keep_parents=False):
        for rol in self.roles.all():
            for perm in rol.permissions.all():
                remove_perm(perm.codename, self.usuario, self.proyecto)
        super(MiembroEquipo, self).delete(using, keep_parents)


class Sprint(models.Model):
    """
    Modelo que representa los sprints del proyecto.
    """
    proyecto = models.ForeignKey(Proyecto)
    nombre = models.CharField(max_length=30)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    def __unicode__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse_lazy('sprint_detail', args=[self.pk])

    class Meta:
        default_permissions = ()
        verbose_name_plural = 'sprints'
        verbose_name = 'sprint'


class Flujo(models.Model):
    """
    Los flujos que forman parte de un proyecto.
    """
    nombre = models.CharField(max_length=30)
    proyecto = models.ForeignKey(Proyecto)

    def __unicode__(self):
        return self.nombre

    class Meta:
        default_permissions = ()
        verbose_name = 'flujo'
        verbose_name_plural = 'flujos'


class Actividad(models.Model):
    """
    Las actividades representan las distintas etapas de las que se compone un flujo.
    """

    nombre = models.CharField(max_length=30)
    flujo = models.ForeignKey(Flujo)

    def __unicode__(self):
        return self.nombre

    class Meta:
        order_with_respect_to = 'flujo'


class UserStory(models.Model):
    """
     Manejo de los User Stories. Los User Stories representan a cada
    funcionalidad desde la perspectiva del cliente que debe realizar el sistema.
    """
    ACTIVIDAD_ESTADOS = (
        (1, 'A Hacer'),
        (2, 'Haciendo'),
        (3, 'Hecho')
    )
    ESTADOS = (
        (1, 'Inactivo'),
        (2, 'En Curso'),
        (3, 'Pendiente de Aprobacion'),
        (4, 'Aprobado'),
        (5, 'Cancelado')
    )
    PRIORIDADES = (
        (1, 'Baja'),
        (2, 'Media'),
        (3, 'Alta')
    )

    nombre = models.CharField(max_length=60)
    descripcion = models.TextField()
    prioridad = models.IntegerField(default=1, choices=PRIORIDADES)
    valor_negocio = models.IntegerField()
    valor_tecnico = models.IntegerField()
    tiempo_estimado = models.PositiveIntegerField()
    tiempo_registrado = models.PositiveIntegerField(default=0)
    ultimo_cambio = models.DateTimeField(auto_now=True)
    estado = models.IntegerField(default=1, choices=ESTADOS)
    estado_actividad = models.IntegerField(default=1, choices=ACTIVIDAD_ESTADOS)
    proyecto = models.ForeignKey(Proyecto)
    desarrolador = models.ForeignKey('auth.User', null=True, blank=True)
    sprint = models.ForeignKey(Sprint, null=True, blank=True)
    actividad = models.ForeignKey(Actividad, null=True, blank=True)

    def __unicode__(self):
        return self.nombre

    def _get_progreso(self):
        progreso = float(self.tiempo_registrado) / self.tiempo_estimado * 100 #porcentaje del progreso
        return int(progreso if progreso <= 100 else 100)
    progreso = property(_get_progreso)

    def get_absolute_url(self):
        return reverse_lazy('us_detail', args=[self.pk])

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        old_dev = None

        # si ya existe el objeto.
        if self.pk is not None:
            old_instance = get_object_or_404(UserStory, pk=self.pk)
            old_dev = old_instance.desarrolador
        super(UserStory, self).save(force_insert, force_update, using, update_fields)

        if old_dev and old_dev is not self.desarrolador:
            for perm in get_perms(old_dev, self):
                remove_perm(perm, old_dev, self)

            if self.proyecto and self.desarrolador:
                memebership = get_object_or_404(
                    MiembroEquipo, usuario=self.desarrolador, proyecto=self.proyecto
                )
                permisos_us = get_perms_for_model(UserStory)
                for rol in memebership.roles.all():
                    for perm in rol.permissions.all():
                        if perm in permisos_us:
                            assign_perm(perm.codename, self.desarrolador, self)

    class Meta:
        default_permissions = ()
        permissions = (
            ('edit_my_us', 'editar mis user stories'),
            ('register_my_us', 'registrar avances en mi user story'),
        )
        verbose_name = 'user story'
        verbose_name_plural = 'user stories'


reversion.register(
    UserStory,
    fields=[
        'nombre', 'descripcion', 'prioridad', 'valor_negocio', 'valor_tecnico', 'tiempo_estimado'
    ]
)

from core.signals import add_permissions_team_member
m2m_changed.connect(add_permissions_team_member, sender=MiembroEquipo.roles.through,
                    dispatch_uid='add_permissions_signal')

