# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-28 12:57
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0007_alter_validators_add_error_messages'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Actividad',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Flujo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=30)),
            ],
            options={
                'default_permissions': (),
                'verbose_name': 'flujo',
                'verbose_name_plural': 'flujos',
            },
        ),
        migrations.CreateModel(
            name='MiembroEquipo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Miembros del Equipo',
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='Proyecto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_corto', models.CharField(max_length=20)),
                ('nombre_largo', models.CharField(max_length=40)),
                ('estado', models.CharField(choices=[('EP', 'En Produccion'), ('CO', 'Completado'), ('AP', 'Aprobado'), ('CA', 'Cancelado'), ('IN', 'Inactivo')], default='IN', max_length=2)),
                ('fecha_inicio', models.DateField(default=django.utils.timezone.now)),
                ('fecha_fin', models.DateField()),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('duracion_sprint', models.PositiveIntegerField(default=30)),
                ('descripcion', models.TextField()),
                ('equipo', models.ManyToManyField(through='core.MiembroEquipo', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'permissions': (('list_all_projects', 'listar los proyectos disponibles'), ('view_project', 'ver el proyecto'), ('aprove_project', 'aprobar el proyecto'), ('create_sprint', 'agregar sprint'), ('edit_sprint', 'editar sprint'), ('remove_sprint', 'eliminar sprint'), ('create_flujo', 'agregar flujo'), ('edit_flujo', 'editar flujo'), ('remove_flujo', 'eliminar flujo'), ('create_us', 'agregar user story'), ('edit_us', 'editar user story'), ('remove_us', 'eliminar user story'), ('prior_us', 'asignar prioridad a user story'), ('regactivity_us', 'registrar avances en user stories'), ('aprove_us', 'aprobar user stories completados'), ('cancel_us', 'cancelar user stories completados')),
            },
        ),
        migrations.CreateModel(
            name='Sprint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=30)),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField()),
                ('proyecto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Proyecto')),
            ],
            options={
                'default_permissions': (),
                'verbose_name': 'sprint',
                'verbose_name_plural': 'sprints',
            },
        ),
        migrations.CreateModel(
            name='UserStory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=60)),
                ('descripcion', models.TextField()),
                ('prioridad', models.IntegerField(choices=[(1, 'Baja'), (2, 'Media'), (3, 'Alta')], default=1)),
                ('valor_negocio', models.IntegerField()),
                ('valor_tecnico', models.IntegerField()),
                ('tiempo_estimado', models.PositiveIntegerField()),
                ('tiempo_registrado', models.PositiveIntegerField(default=0)),
                ('ultimo_cambio', models.DateTimeField(auto_now=True)),
                ('estado', models.IntegerField(choices=[(1, 'Inactivo'), (2, 'En Curso'), (3, 'Pendiente de Aprobacion'), (4, 'Aprobado'), (5, 'Cancelado')], default=1)),
                ('estado_actividad', models.IntegerField(choices=[(1, 'A Hacer'), (2, 'Haciendo'), (3, 'Hecho')], default=1)),
                ('actividad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Actividad')),
                ('desarrolador', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('proyecto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Proyecto')),
                ('sprint', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Sprint')),
            ],
            options={
                'default_permissions': (),
                'verbose_name': 'user story',
                'verbose_name_plural': 'user stories',
                'permissions': (('edit_my_us', 'editar mis user stories'), ('register_my_us', 'registrar avances en mi user story')),
            },
        ),
        migrations.AddField(
            model_name='miembroequipo',
            name='proyecto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Proyecto'),
        ),
        migrations.AddField(
            model_name='miembroequipo',
            name='roles',
            field=models.ManyToManyField(to='auth.Group'),
        ),
        migrations.AddField(
            model_name='miembroequipo',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='flujo',
            name='proyecto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Proyecto'),
        ),
        migrations.AddField(
            model_name='actividad',
            name='flujo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Flujo'),
        ),
        migrations.AlterUniqueTogether(
            name='miembroequipo',
            unique_together=set([('usuario', 'proyecto')]),
        ),
        migrations.AlterOrderWithRespectTo(
            name='actividad',
            order_with_respect_to='flujo',
        ),
    ]
