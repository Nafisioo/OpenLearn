from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson, Enrollment
from quizzes.models import Quiz
User = get_user_model()

client = APIClient()
u = User.objects.create_user(username="debuguser", password="pw")
instr = User.objects.create_user(username="instrX", password="pw")
course = Course.objects.create(title="C1", description="d", instructor=instr)
lesson = Lesson.objects.create(course=course, title="L1", content="c", order=1)
quiz = Quiz.objects.create(lesson=lesson, title="Q1", description="d")
Enrollment.objects.create(user=u, course=course)

client.force_authenticate(user=u)
url = reverse("attempt-list")
print("POSTing to", url)
r = client.post(url, {"quiz": quiz.id}, format="json")
print("status:", r.status_code)
print("data:", r.data if hasattr(r, "data") else r.content)
