from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Permission, User, Group
from django.forms.models import BaseInlineFormSet
from guardian.shortcuts import get_perms_for_model

from core.models import Proyecto


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
    perms_proyecto_list = [(perm.codename, perm.name) for perm in get_perms_for_model(Proyecto) if 'proyecto' in perm.codename]

    perms_proyecto = forms.MultipleChoiceField(
        perms_proyecto_list,
        widget=forms.CheckboxSelectMultiple,
        label=Proyecto._meta.verbose_name_plural.title(),
        required=False
    )

    class Meta:
        model = Group
        fields = ('name',)







