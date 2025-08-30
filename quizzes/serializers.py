from rest_framework import serializers
from django.utils import timezone
from .models import Quiz, Question, Choice, QuizAttempt, Answer

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]
        read_only_fields = ["is_correct"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    class Meta:
        model = Question
        fields = ["id", "text", "order", "type", "choices"]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    course = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Quiz
        fields = ("id", "title", "description", "course", "random_order", "single_attempt", "pass_mark", "draft", "questions", "created_at")


class AnswerSubmitSerializer(serializers.Serializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    selected_choice = serializers.PrimaryKeyRelatedField(queryset=Choice.objects.all(), required=False, allow_null=True)
    free_response = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        q = data["question"]
        if q.type == Question.MULTIPLE_CHOICE and data.get("selected_choice") is None:
            raise serializers.ValidationError("MCQ questions require a selected_choice.")
        if q.type == Question.ANATOMICAL and not data.get("free_response"):
            raise serializers.ValidationError("Anatomical questions require free_response.")
        return data
    

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ("id", "question", "selected_choice", "free_response")



class AttemptSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    score = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ("id", "quiz", "user", "attempt_number", "started_at", "completed_at", "score", "answers")
        read_only_fields = ("id", "user", "attempt_number", "started_at", "completed_at", "score", "answers")

    def compute_score(self, attempt):
        mcq_qs = list(attempt._mcq_questions())
        total = len(mcq_qs)
        if total == 0:
            return 0.0, 0, 0

        # fetch answers keyed by question_id
        answers = {a.question_id: a for a in attempt.answers.select_related("selected_choice").all()}
        correct = 0
        for q in mcq_qs:
            ans = answers.get(q.id)
            if ans and ans.selected_choice and getattr(ans.selected_choice, "is_correct", False):
                correct += 1

        percentage = (correct / total) * 100.0
        return float(round(percentage, 2)), correct, total

    def complete_attempt(self, attempt):
        score, correct, total = self.compute_score(attempt)
        attempt.score = score
        attempt.completed_at = timezone.now()
        attempt.save(update_fields=["score", "completed_at"])
        return score
