from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User, AnonymousUser


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