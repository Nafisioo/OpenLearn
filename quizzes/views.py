from django.utils import timezone
from django.db import IntegrityError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Quiz, QuizAttempt, Answer, Question
from .serializers import QuizSerializer, AttemptSerializer, AnswerSubmitSerializer
from .permissions import IsEnrolledInCourse, IsFirstQuizAttempt
from courses.models import Enrollment


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsEnrolledInCourse]

    def get_queryset(self):
        user = self.request.user
        course_ids = Enrollment.objects.filter(user=user).values_list("course_id", flat=True)
        return Quiz.objects.filter(lesson__course_id__in=course_ids)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsEnrolledInCourse, IsFirstQuizAttempt],
    )
    def start(self, request, pk=None):
        quiz = self.get_object()
        try:
            enrollment = Enrollment.objects.get(user=request.user, course=quiz.lesson.course)
        except Enrollment.DoesNotExist:
            return Response({"detail": "Not enrolled."}, status=status.HTTP_403_FORBIDDEN)

        if QuizAttempt.objects.filter(enrollment=enrollment, quiz=quiz).exists():
            return Response({"detail": "Attempt already exists."}, status=status.HTTP_400_BAD_REQUEST)

        attempt = QuizAttempt.objects.create(enrollment=enrollment, quiz=quiz, started_at=timezone.now())
        serializer = AttemptSerializer(attempt, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all()
    serializer_class = AttemptSerializer
    permission_classes = [IsAuthenticated, IsEnrolledInCourse, IsFirstQuizAttempt]

    def get_queryset(self):
        return QuizAttempt.objects.filter(enrollment__user=self.request.user)

    def create(self, request, *args, **kwargs):
        quiz_id = request.data.get("quiz")
        if not quiz_id:
            return Response({"detail": "Missing 'quiz' field."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except Quiz.DoesNotExist:
            return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            enrollment = Enrollment.objects.get(user=request.user, course=quiz.lesson.course)
        except Enrollment.DoesNotExist:
            return Response({"detail": "You are not enrolled in this course."}, status=status.HTTP_403_FORBIDDEN)

        if QuizAttempt.objects.filter(enrollment=enrollment, quiz=quiz).exists():
            return Response({"detail": "Attempt already exists."}, status=status.HTTP_400_BAD_REQUEST)

        attempt = QuizAttempt.objects.create(enrollment=enrollment, quiz=quiz, started_at=timezone.now())
        serializer = self.get_serializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def answer(self, request, pk=None):
        attempt = self.get_object()
        if attempt.enrollment.user != request.user:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        serializer = AnswerSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        selected_choice = serializer.validated_data.get("selected_choice")
        free_response = serializer.validated_data.get("free_response", "")

        if question.quiz_id != attempt.quiz_id:
            return Response({"detail": "Question does not belong to this quiz/attempt."}, status=status.HTTP_400_BAD_REQUEST)

        if selected_choice and selected_choice.question_id != question.id:
            return Response({"detail": "Selected choice does not belong to the given question."}, status=status.HTTP_400_BAD_REQUEST)

        defaults = {
            "selected_choice": selected_choice,
            "free_response": free_response,
        }

        answer, created = Answer.objects.get_or_create(
            attempt=attempt,
            question=question,
            defaults=defaults,
        )
        if not created:
            answer.selected_choice = selected_choice
            answer.free_response = free_response
            answer.save()

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({"detail": "Answer recorded"}, status=status_code)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        attempt = self.get_object()
        if attempt.enrollment.user != request.user:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        mcq_questions_qs = attempt.quiz.questions.filter(type=Question.MULTIPLE_CHOICE)
        total_mcq = mcq_questions_qs.count()

        mcq_answers = attempt.answers.filter(question__type=Question.MULTIPLE_CHOICE)
        correct = sum(1 for ans in mcq_answers if ans.selected_choice and ans.selected_choice.is_correct)

        score = (correct / total_mcq * 100.0) if total_mcq else 0.0
        attempt.score = score
        attempt.completed_at = timezone.now()
        attempt.save(update_fields=["score", "completed_at"])
        return Response({"score": float(score)}, status=status.HTTP_200_OK)
