import datetime

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Permission, User, Group
from django.core.exceptions import ValidationError
from django.forms.formsets import BaseFormSet
from django.forms.models import BaseInlineFormSet
from django.utils import timezone
from guardian.shortcuts import get_perms_for_model

from core.models import Proyecto, Sprint, Flujo, UserStory


def __general_perms_list__():
    """
    Devuelve una lista de permisos generales
    :return: lista con los permisos que pueden asignarse a nivel general
    :rtype: list
    """
    permlist = []
    permlist.append(Permission.objects.get(codename="list_all_projects"))
    permlist.append(Permission.objects.get(codename="add_proyecto"))
    return permlist


def __user_and_group_permissions__():
    """
    perimisos de grupos de usuarios
    :return: lista con los permisos que pueden asignarse a usuarios
    """
    perms_user_list = [(perm.codename, perm.name) for perm in get_perms_for_model(User)]
    perms_group_list = [(perm.codename, perm.name) for perm in get_perms_for_model(Group)]
    perms = []
    perms.extend(perms_user_list)
    perms.extend(perms_group_list)
    return perms


class UserCreateForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    perms_list = [(perm.codename, perm.name) for perm in __general_perms_list__()]
    perms_list.extend(__user_and_group_permissions__())
    general_perms = forms.MultipleChoiceField(
        perms_list,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Permisos Generales'
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')


class UserEditForm(UserChangeForm):
    perms_list = [(perm.codename, perm.name) for perm in __general_perms_list__()]
    perms_list.extend(__user_and_group_permissions__())
    general_perms = forms.MultipleChoiceField(
        perms_list,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Permisos Generales'
    )


class RolForm(forms.ModelForm):
    perms_proyecto_list = [(perm.codename, perm.name) for perm in get_perms_for_model(Proyecto) if 'project' in perm.codename]
    perms_us_list = [(perm.codename, perm.name) for perm in get_perms_for_model(Proyecto) if 'us' in perm.codename]
    perms_flujo_list = [(perm.codename, perm.name) for perm in get_perms_for_model(Proyecto) if 'flujo' in perm.codename]
    perms_sprint_list = [(perm.codename, perm.name) for perm in get_perms_for_model(Proyecto) if 'sprint' in perm.codename]

    perms_proyecto = forms.MultipleChoiceField(
        perms_proyecto_list,
        widget=forms.CheckboxSelectMultiple,
        label=Proyecto._meta.verbose_name_plural.title(),
        required=False
    )

    perms_us = forms.MultipleChoiceField(
        perms_us_list,
        widget=forms.CheckboxSelectMultiple,
        label=UserStory._meta.verbose_name_plural.title(),
        required=False
    )

    perms_flujo = forms.MultipleChoiceField(
        perms_flujo_list,
        widget=forms.CheckboxSelectMultiple,
        label=Flujo._meta.verbose_name_plural.title(),
        required=False
    )

    perms_sprint = forms.MultipleChoiceField(
        perms_sprint_list,
        widget=forms.CheckboxSelectMultiple,
        label=Sprint._meta.verbose_name_plural.title(),
        required=False
    )

    class Meta:
        model = Group
        fields = ('name',)


class FlujoCreateForm(forms.ModelForm):
    class Meta:
        model = Flujo
        fields = ('nombre',)

# TODO ActividadFormSet poner en views


class SprintCreateBaseForm(forms.ModelForm):
    class Meta:
        model = Sprint
        fields = ('nombre', 'fecha_inicio', 'fecha_fin')

    def clean(self):
        """
        Se chequea que las fechas de los sprint no se solapen
        """

        # si existe algun error en el form no se hace validaciones
        if any(self.erros):
            return

        if 'fecha_inicio' and 'proyecto' in self.cleaned_data:
            fecha_inicio = self.cleaned_data['fecha_inicio']
            proyecto = self.cleaned_data['proyecto']

            fin = fecha_inicio + datetime.timedelta(days=proyecto.duracion_sprint)
            hoy = timezone.now().date()
            sprint = proyecto.sprint_set.filter(fecha_inicio__lte=fin, fecha_fin_gte=fecha_inicio).exclude(pk=self.instance.pk)
            if (fecha_inicio.date() < hoy) and (fecha_inicio is not self.instance.fecha_inicio):
                raise ValidationError({'fecha_inicio': 'Fecha de inicio debe ser mayor o igual a la fecha actual'})
            if sprint.exists():
                raise ValidationError({'fecha_inicio': 'Durante este periodo ya existe el sprint ' + str(sprint[0].nombre)})
            if fecha_inicio.date() < proyecto.fecha_inicio.date():
                raise ValidationError({'fecha_inicio': 'Fecha de inicio debe ser mayor a la fecha de inicio del proyecto.'})
            if fecha_inicio.date() >= proyecto.fecha_fin.date():
                raise ValidationError({'fecha_inicio': 'Fecha de inicio debe ser menor a la fecha de fin del proyecto'})
            if fin.date() > proyecto.fecha_fin.date():
                raise ValidationError({'fecha_inicio': 'Fin del sprint supera la fecha de fin del proyecto'})


class AddToSprintForm(forms.Form):
    userstory = forms.ModelChoiceField(queryset=UserStory.objects.all())
    desarrolador = forms.ModelChoiceField(queryset=User.objects.all())
    flujo = forms.ModelChoiceField(queryset=Flujo.objects.all())


class SprintFormSet(BaseFormSet):
    def clean(self):
        # si algun form del formset tiene errores, no se valida, se retorna directo
        if any(self.errors):
            return

        us_list = []

        for form in self.forms:
            if 'userstory' in form.cleaned_data and not form in self.deleted_forms:
                us = form.cleaned_data['userstory']
                if us in us_list:
                    raise forms.ValidationError('Un mismo User Story solo puede aparecer una vez en el sprint.')
                us_list.append(us)

