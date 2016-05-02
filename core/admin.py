from django.contrib import admin

from core.models import MiembroEquipo, Proyecto


class MiembroEquipoInline(admin.TabularInline):
    model = MiembroEquipo
    extra = 3


class ProyectoAdmin(admin.ModelAdmin):
    inlines = [MiembroEquipoInline,]

admin.site.register(Proyecto, ProyectoAdmin)
