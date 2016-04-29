from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.list import ListView

from core.models import Proyecto


def index_view(request):

    """
       Metodo que redirecciona a la pagina de inicio si esta autenticado el usuario

       @param request: Http request
       @type  request: Htttptrequest
       @return: render al template del index
    """

    if request.user.is_authenticated():
        """
        si el usuario esta autenticado
        """
        return render(request, 'core/index.html')

    return HttpResponseRedirect('/login')


class ProjectList(LoginRequiredMixin, ListView):
    # listado de los proyectos de acuerdo a los permisos de usuario autenticado
    model = Proyecto
    context_object_name = 'projects'
    template_name = 'core/projects/project_list.html'

    def get_queryset(self):
        if self.request.user.has_perm('core.list_all_projects'):
            proyectos = Proyecto.objects.all()
        else:
            proyectos = self.request.user.proyecto_set
        return proyectos.exclude(estado='CA')

project_list = ProjectList.as_view()

