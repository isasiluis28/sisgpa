from guardian.shortcuts import assign_perm

from core.models import UserStory


def add_permissions_team_member(sender, **kwargs):
    instance = kwargs['instance']
    action = kwargs['action']
    exceptions = ['edit_my_us', 'register_my_us']

    if action == 'post_add':
        for rol in instance.roles.all():
            for perm in rol.permissions.all():
                if not perm.codename in exceptions:
                    # copiar los permisos de cada rol para con ese proyecto
                    assign_perm(perm.codename, instance.usuario, instance.proyecto)
                else:
                    # copiar los permisos de us en el proyecto
                    us_list = UserStory.objects.get(proyecto=instance.proyecto, desarrolador=instance.usuario)
                    for us in us_list:
                        assign_perm(perm.codename, instance.usuario, us)

