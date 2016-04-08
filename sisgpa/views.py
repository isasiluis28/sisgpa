from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout

def login_view(request):

    """
           Metodo que se encarga de mostrar login en el sistema
           si el usuario esta autenticado, se le redirige
           a la vista de index.

           @param  request:Http request
           @type   request: HttptRequest
           @return :render al template de login
    """

    if request.user.is_authenticated():


        return HttpResponseRedirect('/home/')

    else:

        """
        si el usuario aun no fue autenticado, se ve si existe algun
        post, sino se renderiza la pagina de inicio de sesion.

        """
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)

            if user is not None:
                """
                si el usuario existe.
                """
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect('/home/')
                else:
                    mensaje = 'Su cuenta ha sido desabilitada, contacte con el administrador para mayores detalles.'
                    return render(request, 'sisgpa/login.html', {'mensaje': mensaje})
            else:
                mensaje = 'Datos proveidos incorrectos, vuelva a intentar.'
                return render(request, 'sisgpa/login.html', {'mensaje': mensaje})

        return render(request, 'sisgpa/login.html')


def index_view(request):
    """
       Metodo que redirecciona a la pagina de inicio si esta autenticado el usuario

       @param request: Http request
       @type  request: Htttptrequest
       @return: render al template del index
    """

    if request.user.is_authenticated():
        """
        si el usuario esta autenticado.
        """
        return render(request, 'sisgpa/index.html')

    return HttpResponseRedirect('/')


