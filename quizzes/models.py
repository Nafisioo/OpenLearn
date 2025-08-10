from django.conf import settings
from django.db import models
from courses.models import Lesson, Enrollment
from django.core.exceptions import ValidationError


User = settings.AUTH_USER_MODEL


class Quiz(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="quizzes"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} (Lesson: {self.lesson.title})"


class Question(models.Model):
    MULTIPLE_CHOICE = "mcq"
    ANATOMICAL      = "anat"

    QUESTION_TYPES = [
        (MULTIPLE_CHOICE, "Multiple Choice"),
        (ANATOMICAL,      "Anatomical / Free Response"),
    ]

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    text = models.TextField()
    order = models.PositiveIntegerField()
    type      = models.CharField(max_length=4, choices=QUESTION_TYPES, default=MULTIPLE_CHOICE)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]} [{self.get_type_display()}]"


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices"
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        prefix = "✔" if self.is_correct else "✘"
        return f"{prefix} {self.text}"


class QuizAttempt(models.Model):
    """
    When a user takes a quiz, we record an attempt.
    """
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
        null=True,
        blank=True,
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
        null=True,
        blank=True,
    )
    started_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage score from 0.00 to 100.00",
        null=True,
        blank=True,

    )

    class Meta:
        unique_together = ("enrollment", "quiz")

    def __str__(self):
        return f"{self.enrollment.user.username} on {self.quiz.title}"


class Answer(models.Model):
    """
    Stores the choice a user selected for a given question in a QuizAttempt.
    """
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        null=True, blank=True, related_name="+",
        help_text="Which MCQ choice they picked (if MCQ)",
    )
    free_response   = models.TextField(
                        null=True, blank=True,
                        help_text="User’s free-form/anatomical answer"
                      )

    class Meta:
        unique_together = ("attempt", "question")

    def clean(self):
        if self.question.type == Question.MULTIPLE_CHOICE:
            if self.selected_choice is None:
                raise ValidationError("Must select one of the MCQ choices.")
        else: 
            if not self.free_response:
                raise ValidationError("Must provide a free‐form/anatomical response.")

    def __str__(self):
        user = self.attempt.enrollment.user.username
        if self.question.type == Question.MULTIPLE_CHOICE:
            return f"{user}: Q{self.question.order} → {self.selected_choice.text[:30]}"
        return f"{user}: Q{self.question.order} → {self.free_response[:30]}"

