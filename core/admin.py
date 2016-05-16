from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from core.models import MiembroEquipo, Proyecto, Actividad, Flujo, UserStory, Sprint


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


class UserStoryAdmin(GuardedModelAdmin):
    pass

admin.site.register(Proyecto, ProyectoAdmin)
admin.site.register(Flujo, FlujoAdmin)
admin.site.register(UserStory, UserStoryAdmin)
admin.site.register(Sprint)
