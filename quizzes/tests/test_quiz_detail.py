from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson, Enrollment
from quizzes.models import Quiz, Question, Choice

User = get_user_model()

class QuizDetailTest(APITestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(username="instr", password="pass")
        self.student = User.objects.create_user(username="student", password="pass")
        self.course = Course.objects.create(title="Course", description="d", instructor=self.instructor)
        self.lesson = Lesson.objects.create(course=self.course, title="Lesson", content="c", order=1)
        self.quiz = Quiz.objects.create(lesson=self.lesson, title="Lesson Quiz", description="desc")
        q1 = Question.objects.create(quiz=self.quiz, text="Q1", order=1)
        Choice.objects.create(question=q1, text="Opt1", is_correct=True)
        Choice.objects.create(question=q1, text="Opt2", is_correct=False)

    def test_quiz_detail_includes_questions_and_choices(self):
        Enrollment.objects.create(user=self.student, course=self.course)
        self.client.force_authenticate(user=self.student)
        url = reverse("quiz-detail", args=[self.quiz.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("id"), self.quiz.id)
        questions = data.get("questions")
        self.assertIsInstance(questions, list)
        first_q = questions[0]
        self.assertIsInstance(first_q.get("choices"), list)
