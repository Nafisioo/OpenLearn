from rest_framework.permissions import BasePermission
from .models import QuizAttempt, Quiz
from courses.models import Course

class IsEnrolledInCourse(BasePermission):
    """
    Allow access only if request.user is enrolled in quiz.course via Course.students M2M.
    """
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        if request.method == "POST" and "quiz" in request.data:
            quiz_id = request.data.get("quiz")
            try:
                quiz = Quiz.objects.select_related("course").get(pk=quiz_id)
            except Quiz.DoesNotExist:
                return False
            course = getattr(quiz, "course", None)
            if course is None:
                return False
            return course.students.filter(pk=user.pk).exist()
        return True

    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        if isinstance(obj, Quiz):
            course = getattr(obj, "course", None)
        elif isinstance(obj, QuizAttempt):
            course = getattr(obj.quiz, "course", None)
        else:
            return False

        if course is None:
            return False

        return course.students.filter(pk=user.pk).exists()


class IsFirstQuizAttempt(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        if request.method != "POST":
            return True

        quiz_id = request.data.get("quiz")
        if not quiz_id:
            return True
        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except Quiz.DoesNotExist:
            return True
        if quiz.single_attempt and quiz.attempts.filter(user=user, completed_at__isnull=False).exist():
            return False
        return True