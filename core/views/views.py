from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponseRedirect
from django.shortcuts import render

from guardian.mixins import PermissionRequiredMixin

from core.models import Proyecto, MiembroEquipo


class GlobalPermissionMixin(PermissionRequiredMixin):
    accept_global_perms = True
    raise_exception = True
    return_403 = True


class CreateViewMixin(GlobalPermissionMixin):
    def get_object(self):
        return None


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


def get_selected_perms(POST):
    perm_list = POST.getlist('perms_proyecto')
    return perm_list


class ActiveProjectRequiredMixin(object):
    proyecto = None

    def get_proyecto(self):
        return self.proyecto

    def dispatch(self, request, *args, **kwargs):
        proyecto = self.get_proyecto()
        if proyecto.estado != 'AP':
            return super(ActiveProjectRequiredMixin, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()










