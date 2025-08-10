from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson, Enrollment
from quizzes.models import Quiz, Question, Choice

User = get_user_model()

class QuizListTest(APITestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(username="instr", password="pass")
        self.student = User.objects.create_user(username="student", password="pass")
        self.course = Course.objects.create(title="C1", description="d", instructor=self.instructor)
        self.lesson = Lesson.objects.create(course=self.course, title="L1", content="c", order=1)
        self.quiz = Quiz.objects.create(lesson=self.lesson, title="Qz", description="desc")
        q = Question.objects.create(quiz=self.quiz, text="What?", order=1)
        Choice.objects.create(question=q, text="A", is_correct=True)
        Choice.objects.create(question=q, text="B", is_correct=False)

    def test_requires_authentication(self):
        url = reverse("quiz-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 401)

    def test_enrolled_user_sees_quiz(self):
        Enrollment.objects.create(user=self.student, course=self.course)
        self.client.force_authenticate(user=self.student)
        url = reverse("quiz-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        ids = [item.get("id") for item in data if isinstance(item, dict)]
        self.assertIn(self.quiz.id, ids)
