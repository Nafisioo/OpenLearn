from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from accounts.models import User
from core.models import SiteFeedback
from rest_framework_simplejwt.tokens import RefreshToken

class SiteFeedbackAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='feedbackuser',
            password='testpass'
        )
        refresh = RefreshToken.for_user(cls.user)
        cls.token = str(refresh.access_token)
        cls.url = reverse('site-feedback') 

    def test_submit_and_list_feedback(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        payload = {
            'message': 'Great LMS so far!',
            'rating': 4
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SiteFeedback.objects.count(), 1)
        fb = SiteFeedback.objects.first()
        self.assertEqual(fb.message, payload['message'])
        self.assertEqual(fb.rating, payload['rating'])
        self.assertEqual(fb.user, self.user)

    def test_auth_required(self):
        response = self.client.post(self.url, {'message': 'X', 'rating': 3}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)