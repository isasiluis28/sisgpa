from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User, Group, Permission
from django.utils import timezone
from core.models import Proyecto



class LoginTest(TestCase):
    def setUp(self):
        User.objects.create_user('test', 'test@test.com', 'password')

    def test_login_existing_user(self):
        u = User.objects.get(username='test')
        self.assertIsNotNone(u)
        c = self.client
        login = c.login(username='test', password='password')
        self.assertTrue(login)

    def test_login_wrong_password(self):
        u = User.objects.get(username='test')
        self.assertIsNotNone(u)
        c = self.client
        pw = 'wrong_password'
        login = c.login(username='test', password=pw)
        self.assertFalse(login)


class ProyectoTest(TestCase):
    def setUp(self):
        usuario = User.objects.create_superuser("user", "user@email.com", "password")
        permiso = Permission.objects.get(codename="add_proyecto")
        usuario.user_permissions.add(permiso)
        permiso = Permission.objects.get(codename='change_proyecto')
        usuario.user_permissions.add(permiso)
        permiso = Permission.objects.get(codename='delete_proyecto')
        usuario.user_permissions.add(permiso)
        u = User.objects.create_user('fulano', 'temp@email.com', 'temp')
        pro = Proyecto.objects.create(nombre_corto='Proyecto',
                                      nombre_largo='Proyecto Largo',
                                      estado='IN',
                                      fecha_inicio=timezone.now(),
                                      fecha_fin=timezone.now(),
                                      fecha_creacion='2016-04-30 17:00',
                                      descripcion='Test test')
        Group.objects.create(name='rol')

    def test_permission_to_create_proyecto(self):
        c = self.client
        self.assertTrue(c.login(username="user", password="password"))
        response = c.get('/projects/add/')
        self.assertEquals(response.status_code, 200)

    def test_permission_to_change_proyecto(self):
        c = self.client
        self.assertTrue(c.login(username='user', password='password'))
        response = c.get('/projects/1/edit/')
        self.assertEquals(response.status_code, 200)


class UserTest(TestCase):
    def setUp(self):
        u = User.objects.create_user('user', 'user@email.com', 'password')
        p = Permission.objects.get(codename='add_user')
        u.user_permissions.add(p)
        p = Permission.objects.get(codename='change_user')
        u.user_permissions.add(p)
        p = Permission.objects.get(codename='delete_user')
        u.user_permissions.add(p)
        u = User.objects.create_user('usuario_prueba','temp@email.com', 'password2')

    def test_create_user(self):
        c = self.client
        self.assertTrue(c.login(username='user', password='password'))
        response = c.get('/users/add/')
        self.assertEquals(response.status_code, 200)
        response = c.post('/users/add/', {'first_name': 'Oscar', 'last_name': 'Aguilera', 'username': 'oscar',
                                          'email': 'oscar@email.com', 'password1': 'admin123', 'password2': 'admin123'},
                          follow=True)
        u = User.objects.get(username='oscar')
        # comprobamos que exista el usuario
        self.assertIsNotNone(u)
        # deberia redirigir
        self.assertRedirects(response, '/users/{}/'.format(u.id))

    def test_edit_user(self):
        c = self.client
        self.assertTrue(c.login(username='user', password='password'))
        u = User.objects.get(username='usuario_prueba')
        self.assertIsNotNone(u)
        response = c.get('/users/{}/edit/'.format(u.id))
        self.assertEquals(response.status_code, 200)
        # modificamos los campos: nombre y email
        response = c.post('/users/{}/edit/'.format(u.id), {'username': 'nuevo_username', 'email': 'asd@asd.com'}, follow=True)
        # deberia redirigir
        self.assertRedirects(response, '/users/{}/'.format(u.id))
        # comprobamos el cambio en la bd
        self.assertIsNotNone(User.objects.get(username='nuevo_username'))

    def test_delete_user(self):
        c = self.client
        self.assertTrue(c.login(username='user', password='password'))
        u = User.objects.get(username='usuario_prueba')
        response = c.get('/users/{}/'.format(u.id))
        self.assertEquals(response.status_code, 200)
        #eliminamos el user
        response = c.post('/users/{}/delete/'.format(u.id), {'Confirmar':True}, follow=True)
        self.assertRedirects(response, '/users/')
        #ahora ya no deberia estar activo el usuario
        response = c.get('/users/{}/'.format(u.id))
        self.assertEquals(response.status_code, 200)
        u = User.objects.get(pk=u.id)
        self.assertIsNotNone(u)
        self.assertFalse(u.is_active)

class RolesTest(TestCase):
    def setUp(self):
        u = User.objects.create_user('temp','temp@email.com', 'temp')
        p = Permission.objects.get(codename='add_group')
        u.user_permissions.add(p)
        p = Permission.objects.get(codename='change_group')
        u.user_permissions.add(p)
        p = Permission.objects.get(codename='delete_group')
        u.user_permissions.add(p)

    def create_role(self, name):
        g = Group.objects.create(name=name)
        g.save()
        return g

    def test_create_role(self):
        c = self.client
        self.assertTrue(c.login(username='temp', password='temp'))
        response = c.get('/roles/add/');
        self.assertEquals(response.status_code, 200)
        #intentamos crear un rol developer que pueda crear, editar y borrar proyectos, y crear y borrar US
        response = c.post('/roles/add/', {'name':'developer', 'perms_proyecto':[u'add_proyecto', u'change_proyecto', u'delete_proyecto'], 'perms_userstory':[u'add_userstory',u'delete_userstory']}, follow=True)
        #deberia redirigir
        self.assertEquals(response.status_code, 200)
        response = c.get('/roles/1/')
        self.assertEquals(response.status_code, 404)


    def test_not_create_invalid_role(self):
        c = self.client
        self.assertTrue(c.login(username='temp', password='temp'))
        response = c.get('/roles/add/');
        self.assertEquals(response.status_code, 200)
        #intentamos crear un rol sin nombre
        response = c.post('/roles/add/', {'name':'', 'perms_proyecto':[u'add_proyecto', u'change_proyecto', u'delete_proyecto'], 'perms_userstory':[u'add_userstory',u'delete_userstory']})
        #no deberia redirigir
        self.assertIsNot(response.status_code, 302)
        self.assertContains(response, 'This field is required.')
