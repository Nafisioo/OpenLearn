from rest_framework.permissions import BasePermission
from courses.models import Enrollment
from .models import QuizAttempt, Quiz


class IsEnrolledInCourse(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        if request.method == "POST" and "quiz" in request.data:
            quiz_id = request.data.get("quiz")
            try:
                quiz = Quiz.objects.get(pk=quiz_id)
            except Quiz.DoesNotExist:
                return False
            return Enrollment.objects.filter(user=user, course=quiz.lesson.course).exists()

        return True

    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        if isinstance(obj, Quiz):
            course = obj.lesson.course
        elif isinstance(obj, QuizAttempt):
            enrollment = getattr(obj, "enrollment", None)
            if not enrollment:
                return False
            course = enrollment.course
        else:
            return False

        return Enrollment.objects.filter(user=user, course=course).exists()


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

        return not QuizAttempt.objects.filter(enrollment__user=user, quiz_id=quiz_id).exists()