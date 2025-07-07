from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Course, Enrollment, Lesson, UserLessonProgress
from django.contrib.auth import get_user_model

User = get_user_model()

class CourseAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user = User.objects.create_user(username="user1", password="pass123")
        cls.course = Course.objects.create(
            title="Test Course",
            description="A test course.",
            instructor=cls.user
        )

    def test_course_detail_view(self):
        response = self.client.get(f'/api/courses/{self.course.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.course.title)


class CourseCreationTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(username='adminuser', password='adminpass')
        refresh = RefreshToken.for_user(cls.admin_user)
        cls.access_token = str(refresh.access_token)
        cls.course_url = '/api/courses/create/'
        cls.course_data = {
            "title": "JWT Test Course",
            "description": "Testing course creation with JWT"
        }

    def test_create_course_with_jwt(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post(self.course_url, self.course_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Course.objects.get().title, self.course_data["title"])

    def test_create_course_unauthenticated(self):
        response = self.client.post(self.course_url, self.course_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CourseEnrollmentTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", password="testpass123")
        cls.course = Course.objects.create(
            title="Test Course",
            description="Test Desc",
            instructor=cls.user
        )
        refresh = RefreshToken.for_user(cls.user)
        cls.access_token = str(refresh.access_token)
        cls.url = f"/api/courses/{cls.course.pk}/enroll/"

    def test_enroll_authenticated_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Enrollment.objects.count(), 1)
        self.assertEqual(Enrollment.objects.first().user, self.user)

    def test_enroll_unauthenticated_user(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_enrollment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        self.client.post(self.url)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already enrolled", response.data["detail"].lower())


class EnrolledCoursesListTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='student', password='testpass')
        refresh = RefreshToken.for_user(cls.user)
        cls.access_token = str(refresh.access_token)

        cls.course1 = Course.objects.create(title="Course 1", description="Desc 1", instructor=cls.user)
        cls.course2 = Course.objects.create(title="Course 2", description="Desc 2", instructor=cls.user)

        Enrollment.objects.create(user=cls.user, course=cls.course1)
        cls.url = '/api/courses/my-enrollments/'

    def test_list_enrolled_courses(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], self.course1.title)

    def test_unauthenticated_access(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)


class LessonCompletionTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="student", password="strongpassword")
        cls.course = Course.objects.create(title="Test Course", description="Test Desc", instructor=cls.user)
        cls.lesson = Lesson.objects.create(title="Test Lesson", course=cls.course, content="Some content", order=1)
        cls.enrollment = Enrollment.objects.create(user=cls.user, course=cls.course)

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_complete_lesson(self):
        url = reverse('mark_lesson_complete', args=[self.lesson.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        progress = UserLessonProgress.objects.get(enrollment=self.enrollment, lesson=self.lesson)
        self.assertTrue(progress.completed)
        self.assertEqual(response.data['lesson'], self.lesson.id)
        self.assertEqual(response.data['user']['id'], self.user.id)
        self.assertEqual(response.data['user']['username'], self.user.username)



class CourseProgressTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="progressuser", password="strongpass")
        refresh = RefreshToken.for_user(cls.user)
        cls.access_token = str(refresh.access_token)

        cls.course = Course.objects.create(title="Progress Course", description="Track progress", instructor=cls.user)
        cls.lesson = Lesson.objects.create(course=cls.course, title="Lesson 1", content="Some content", order=1)
        cls.enrollment = Enrollment.objects.create(user=cls.user, course=cls.course)

        UserLessonProgress.objects.create(enrollment=cls.enrollment, lesson=cls.lesson, completed=True)

        cls.url = reverse("course_progress", args=[cls.course.id])

    def test_course_progress(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["course"], self.course.title)
        self.assertEqual(response.data["total_lessons"], 1)
        self.assertEqual(response.data["completed_lessons"], 1)
        self.assertEqual(response.data["progress_percent"], 100)
