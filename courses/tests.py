from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .models import Course, Enrollment, Lesson, UserLessonProgress

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
        url = reverse('course-detail', args=[self.course.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.course.title)


class CourseCreationTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(username='adminuser', password='adminpass')
        refresh = RefreshToken.for_user(cls.admin_user)
        cls.admin_token = str(refresh.access_token)
        cls.course_url = reverse('course-list')
        cls.course_data = {
            "title": "JWT Test Course",
            "description": "Testing course creation with JWT"
        }

    def test_create_course_with_jwt(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.admin_token)
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
        cls.token = str(refresh.access_token)
        cls.url = reverse('course-enroll', args=[cls.course.pk])

    def test_enroll_authenticated_user(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Enrollment.objects.count(), 1)
        self.assertEqual(Enrollment.objects.first().user, self.user)

    def test_enroll_unauthenticated_user(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_enrollment(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        self.client.post(self.url)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already enrolled", response.data["detail"].lower())


class EnrolledCoursesListTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='student', password='testpass')
        refresh = RefreshToken.for_user(cls.user)
        cls.token = str(refresh.access_token)

        cls.course1 = Course.objects.create(title="Course 1", description="Desc 1", instructor=cls.user)
        Course.objects.create(title="Course 2", description="Desc 2", instructor=cls.user)
        Enrollment.objects.create(user=cls.user, course=cls.course1)

        cls.url = reverse('my_enrollments')

    def test_list_enrolled_courses(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], self.course1.title)

    def test_unauthenticated_access(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


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
        cls.token = str(refresh.access_token)

        cls.course = Course.objects.create(title="Progress Course", description="Track progress", instructor=cls.user)
        cls.lesson = Lesson.objects.create(course=cls.course, title="Lesson 1", content="Some content", order=1)
        Enrollment.objects.create(user=cls.user, course=cls.course)
        UserLessonProgress.objects.create(
            enrollment=Enrollment.objects.get(user=cls.user, course=cls.course),
            lesson=cls.lesson,
            completed=True
        )

        cls.url = reverse('course-progress', args=[cls.course.id])

    def test_course_progress(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["course"], self.course.title)
        self.assertEqual(response.data["total_lessons"], 1)
        self.assertEqual(response.data["completed_lessons"], 1)
        self.assertEqual(response.data["progress_percent"], 100)


class CoursePermissionTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin      = User.objects.create_superuser(username='admin', password='adminpass')
        cls.instructor = User.objects.create_user(username='instructor', password='instructorpass')
        cls.other      = User.objects.create_user(username='other', password='otherpass')

        cls.course = Course.objects.create(
            title="Restricted Course",
            description="Sensitive content",
            instructor=cls.instructor
        )

    def get_token(self, user):
        return str(RefreshToken.for_user(user).access_token)

    def test_admin_can_edit_and_delete_course(self):
        token = self.get_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        url = reverse('course-detail', args=[self.course.id])

        # Update
        res = self.client.patch(url, {'title': 'Updated by Admin'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['title'], 'Updated by Admin')

        # Delete
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_instructor_can_edit_own_course(self):
        token = self.get_token(self.instructor)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        url = reverse('course-detail', args=[self.course.id])

        res = self.client.patch(url, {'title': 'Updated by Instructor'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_edit_course(self):
        token = self.get_token(self.other)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        url = reverse('course-detail', args=[self.course.id])

        res = self.client.patch(url, {'title': 'Hacked'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class LessonPermissionTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin      = User.objects.create_superuser(username='admin', password='adminpass')
        cls.instructor = User.objects.create_user(username='instructor', password='instructorpass')
        cls.other      = User.objects.create_user(username='other', password='otherpass')

        cls.course = Course.objects.create(title="Lesson Course", description="Test", instructor=cls.instructor)
        cls.lesson = Lesson.objects.create(course=cls.course, title="Lesson 1", content="Lesson content", order=1)

    def get_token(self, user):
        return str(RefreshToken.for_user(user).access_token)

    def test_admin_can_edit_and_delete_lesson(self):
        token = self.get_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        url = reverse('lesson-detail', args=[self.lesson.id])

        # Update
        res = self.client.patch(url, {'title': 'Admin Changed'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['title'], 'Admin Changed')

        # Delete
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_instructor_can_edit_own_lesson(self):
        token = self.get_token(self.instructor)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        url = reverse('lesson-detail', args=[self.lesson.id])

        res = self.client.patch(url, {'title': 'Instructor Changed'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_edit_lesson(self):
        token = self.get_token(self.other)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        url = reverse('lesson-detail', args=[self.lesson.id])

        res = self.client.patch(url, {'title': 'Not Allowed'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
