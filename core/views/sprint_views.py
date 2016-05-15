from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView
from guardian.mixins import LoginRequiredMixin
from guardian.shortcuts import get_perms

from core.models import Sprint, Proyecto
from core.views.views import GlobalPermissionMixin


class SprintList(LoginRequiredMixin, GlobalPermissionMixin, ListView):
    model = Sprint
    template_name = 'core/sprint/sprint_list.html'
    permission_required = 'core.view_project'
    context_object_name = 'sprints'
    project = None

    def get_objeto(self):
        return get_object_or_404(Proyecto, pk=self.kwargs['project_pk'])

    def get_permission_object(self):
        return self.get_objeto()

    def get_context_data(self, **kwargs):
        context = super(SprintList, self).get_context_data(**kwargs)
        context['proyecto_perms'] = get_perms(self.request.user, self.get_objeto())
        return context

    def get_queryset(self):
        proyecto_pk = self.kwargs['project_pk']
        return Sprint.objects.filter(proyecto=self.get_objeto())

