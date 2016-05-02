from __future__ import unicode_literals

from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import models
from guardian.shortcuts import assign_perm, remove_perm


class Proyecto(models.Model):
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
    descripcion = models.TextField()
    equipo = models.ManyToManyField(User, through='MiembroEquipo')

    class Meta:
        permissions = (
            ('list_all_projects', 'listar los proyectos disponibles'),
            ('view_project', 'ver el proyecto'),
            ('aprove_project', 'aprobar el proyecto'),
        )

    def __unicode__(self):
        return self.nombre_corto

    def clean(self):
        try:
            if self.fecha_inicio > self.fecha_fin:
                raise ValidationError(
                    {'fecha_inicio': 'Fecha de inicio no puede ser mayor a la fecha de fin.'}
                )
        except TypeError:
            # si se trata de una fecha nula, el propio clean del field se encarga de validar
            pass


class MiembroEquipo(models.Model):
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
        # se agrega el permiso de view_project al usuario dentro del proyecto hecho
        assign_perm('view_project', self.usuario, self.proyecto)

    def delete(self, using=None, keep_parents=False):
        for rol in self.roles.all():
            for perm in rol.permissions.all():
                remove_perm(perm.codename, self.usuario, self.proyecto)
        super(MiembroEquipo, self).delete(using, keep_parents)
