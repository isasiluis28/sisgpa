from django.contrib import admin

from core.models import MiembroEquipo, Proyecto, Actividad, Flujo


class MiembroEquipoInline(admin.TabularInline):
    model = MiembroEquipo
    extra = 3


class ActividadInline(admin.TabularInline):
    model = Actividad
    extra = 3


class FlujoAdmin(admin.ModelAdmin):
    inlines = [ActividadInline,]


class ProyectoAdmin(admin.ModelAdmin):
    inlines = [MiembroEquipoInline,]

admin.site.register(Proyecto, ProyectoAdmin)
admin.site.register(Flujo, FlujoAdmin)
