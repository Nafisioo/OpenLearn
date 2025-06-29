from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Course, Enrollment
from django.contrib.auth import get_user_model

User = get_user_model()

class CourseAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.course = Course.objects.create(
            title="Test Course",
            description="A test course."
        )

    def test_course_detail_view(self):
        response = self.client.get(f'/api/courses/{self.course.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.course.title)

class CourseCreationTest(APITestCase):
    def setUp(self):
        # Create an admin user
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            password='adminpass'
        )
        refresh = RefreshToken.for_user(self.admin_user)
        self.access_token = str(refresh.access_token)

        self.course_url = '/api/courses/create/'  
        self.course_data = {
            "title": "JWT Test Course",
            "description": "Testing course creation with JWT"
        }

    def test_create_course_with_jwt(self):
        # Send request with JWT token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post(self.course_url, self.course_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Course.objects.get().title, self.course_data["title"])

    def test_create_course_unauthenticated(self):
        # Send request without token
        response = self.client.post(self.course_url, self.course_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CourseEnrollmentTest(APITestCase):
    def setUp(self):
        # Create test user and course
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.course = Course.objects.create(title="Test Course", description="Test Desc")

        # Generate JWT token for user
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # Enrollment URL using course ID
        self.url = f"/api/courses/{self.course.pk}/enroll/"

    def test_enroll_authenticated_user(self):
        # Send POST with JWT token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Enrollment.objects.count(), 1)
        self.assertEqual(Enrollment.objects.first().user, self.user)

    def test_enroll_unauthenticated_user(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_enrollment(self):
        # First enrollment
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        self.client.post(self.url)

        # Second attempt
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already enrolled", response.data["detail"].lower())
