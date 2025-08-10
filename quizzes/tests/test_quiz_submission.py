from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson, Enrollment
from quizzes.models import Quiz, Question, Choice, QuizAttempt, Answer

User = get_user_model()

class QuizSubmissionTest(APITestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(username="instr", password="pass")
        self.student = User.objects.create_user(username="student", password="pass")
        self.other = User.objects.create_user(username="other", password="pass")
        self.course = Course.objects.create(title="Course", description="d", instructor=self.instructor)
        self.lesson = Lesson.objects.create(course=self.course, title="Lesson", content="c", order=1)
        self.quiz = Quiz.objects.create(lesson=self.lesson, title="Quiz", description="desc")
        self.q1 = Question.objects.create(quiz=self.quiz, text="MCQ Q", order=1, type=Question.MULTIPLE_CHOICE)
        self.c1 = Choice.objects.create(question=self.q1, text="Right", is_correct=True)
        self.c2 = Choice.objects.create(question=self.q1, text="Wrong", is_correct=False)
        self.q2 = Question.objects.create(quiz=self.quiz, text="Free Q", order=2, type=Question.ANATOMICAL)

    def _start_attempt_and_get_id(self):
        url = reverse("attempt-list")
        res = self.client.post(url, {"quiz": self.quiz.id}, format="json")
        if res.status_code in (200, 201):
            payload = res.json()
            if isinstance(payload, dict) and payload.get("id"):
                return payload["id"]
            attempt = QuizAttempt.objects.filter(quiz=self.quiz, enrollment__user=self.client.handler._force_user).first()
            return attempt.id if attempt else None
        return None

    def test_start_requires_enrollment(self):
        self.client.force_authenticate(user=self.other)
        url = reverse("attempt-list")
        res = self.client.post(url, {"quiz": self.quiz.id}, format="json")
        self.assertIn(res.status_code, (403, 404))

    def test_start_and_submit_mcq_authenticated(self):
        Enrollment.objects.create(user=self.student, course=self.course)
        self.client.force_authenticate(user=self.student)
        attempt_id = self._start_attempt_and_get_id()
        self.assertIsNotNone(attempt_id)
        answer_url = reverse("attempt-answer", args=[attempt_id])
        res_ans = self.client.post(answer_url, {"question": self.q1.id, "selected_choice": self.c1.id}, format="json")
        self.assertEqual(res_ans.status_code, 201)
        complete_url = reverse("attempt-complete", args=[attempt_id])
        res_complete = self.client.post(complete_url, {}, format="json")
        self.assertEqual(res_complete.status_code, 200)
        payload = res_complete.json()
        score = payload.get("score") if isinstance(payload, dict) else None
        self.assertIsNotNone(score)
        self.assertAlmostEqual(float(score), 100.0, places=2)

    def test_single_attempt_enforced(self):
        Enrollment.objects.create(user=self.student, course=self.course)
        self.client.force_authenticate(user=self.student)
        url = reverse("attempt-list")
        res1 = self.client.post(url, {"quiz": self.quiz.id}, format="json")
        self.assertIn(res1.status_code, (200, 201))
        res2 = self.client.post(url, {"quiz": self.quiz.id}, format="json")
        self.assertNotIn(res2.status_code, (200, 201))
