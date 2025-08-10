from rest_framework import serializers
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
    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "lesson", "questions", "created_at"]

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

class AttemptSerializer(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()
    score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ["id", "quiz", "started_at", "completed_at", "score", "answers"]
        read_only_fields = ["id", "started_at", "completed_at", "score"]

    def get_answers(self, obj):
        return [
            {
                "question": a.question.id,
                "selected_choice": a.selected_choice.id if a.selected_choice else None,
                "free_response": a.free_response,
                "is_correct": getattr(a.selected_choice, "is_correct", None),
            }
            for a in obj.answers.all()
        ]

