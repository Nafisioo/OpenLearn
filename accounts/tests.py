from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class UserRegistrationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.register_url = reverse('register')
        cls.token_url = reverse('token_obtain_pair')
        cls.admin = User.objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="adminpass"
        )
        refresh = RefreshToken.for_user(cls.admin)
        cls.admin_token = str(refresh.access_token)

        cls.user = User.objects.create_user(
            username="basicuser",
            email="user@example.com",
            password="userpass"
        )
        refresh = RefreshToken.for_user(cls.user)
        cls.user_token = str(refresh.access_token)

    def test_register_student_successfully(self):
        response = self.client.post(self.register_url, {
            "username": "studentuser",
            "email": "student@example.com",
            "password": "testpass123",
            "role": "student"
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('msg', response.data)

    def test_anonymous_cannot_register_as_admin(self):
        response = self.client.post(self.register_url, {
            "username": "baduser",
            "email": "bad@example.com",
            "password": "testpass123",
            "role": "admin"
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('role', response.data)

    def test_admin_can_register_instructor(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.admin_token)
        response = self.client.post(self.register_url, {
            "username": "instructoruser",
            "email": "instructor@example.com",
            "password": "testpass123",
            "role": "instructor"
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('msg', response.data)

    def test_normal_user_cannot_register_instructor(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.user_token)
        response = self.client.post(self.register_url, {
            "username": "intrudeinstructor",
            "email": "intrude@example.com",
            "password": "testpass123",
            "role": "instructor"
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Only admins can assign', str(response.data))
