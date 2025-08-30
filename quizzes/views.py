from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Quiz, QuizAttempt, Answer, Question
from .serializers import QuizSerializer, AttemptSerializer, AnswerSubmitSerializer
from .permissions import IsEnrolledInCourse, IsFirstQuizAttempt
from courses.models import Course


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.all().select_related("course")
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsEnrolledInCourse]

    def get_queryset(self):
        user = self.request.user
        course_ids = Course.objects.filter(Students=user).values_list("id", flat=True)
        return Quiz.objects.filter(course_id__in=course_ids)


class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all().select_related("quiz")
    serializer_class = AttemptSerializer
    permission_classes = [IsAuthenticated, IsEnrolledInCourse, IsFirstQuizAttempt]

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user).select_related("quiz")

    def create(self, request, *args, **kwargs):
        quiz_id = request.data.get("quiz")
        if not quiz_id:
            return Response({"detail": "Missing 'quiz' field."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except Quiz.DoesNotExist:
            return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)

        if not quiz.allow_new_attempt_for_user(request.user):
            return Response({"detail": "You are not allowed another attempt for this quiz."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            attempt = QuizAttempt.objects.start_attempt(user=request.user, quiz=quiz)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"],permission_classes=[IsAuthenticated])
    def answer(self, request, pk=None):
        attempt = self.get_object()
        if attempt.user_id != request.user.id:
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

        answer_obj, created = Answer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults=defaults,
        )

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({"detail": "Answer recorded"}, status=status_code)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        attempt = self.get_object()
        if attempt.user_id != request.user.id:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        mcq_questions_qs = attempt.quiz.questions.filter(type=Question.MULTIPLE_CHOICE)
        total_mcq = mcq_questions_qs.count()

        mcq_answers = attempt.answers.filter(question__type=Question.MULTIPLE_CHOICE)
        correct = sum(1 for ans in mcq_answers if ans.selected_choice and ans.selected_choice.is_correct)

        serializer = AttemptSerializer(context={"request": request})
        score = serializer.complete_attempt(attempt)
        return Response({"score": score}, status=status.HTTP_200_OK)
