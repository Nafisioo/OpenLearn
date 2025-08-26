from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


User = settings.AUTH_USER_MODEL

class Quiz(models.Model):
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="quizzes",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        course_title = getattr(self.course, "title", "No Course")
        return f"{self.title} (Course: {course_title})"


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
    type = models.CharField(max_length=4, choices=QUESTION_TYPES, default=MULTIPLE_CHOICE)

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
   
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quiz_attempts",
        help_text="User who attempted the quiz (nullable to preserve historical attempts)."
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
        unique_together = ("user", "quiz")

    def __str__(self):
        username = getattr(self.user, "username", None) or "UnknownUser"
        quiz_title = getattr(self.quiz, "title", "No Quiz")
        return f"{username} on {quiz_title}"


class Answer(models.Model):
   
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
    free_response = models.TextField(
        null=True, blank=True,
        help_text="User’s free-form/anatomical answer"
    )

    class Meta:
        unique_together = ("attempt", "question")

    def clean(self):
        if self.question.type == Question.MULTIPLE_CHOICE:
            if self.selected_choice is None:
                raise ValidationError("Must select one of the MCQ choices.")
            if self.selected_choice and self.selected_choice.question_id != self.question_id:
                raise ValidationError("Selected choice does not belong to this question.")
        else:
            if not self.free_response:
                raise ValidationError("Must provide a free-form/anatomical response.")

    def __str__(self):
        user = None
        if self.attempt and self.attempt.user:
            user = getattr(self.attempt.user, "username", None)
        user = user or "UnknownUser"
        if self.question.type == Question.MULTIPLE_CHOICE and self.selected_choice:
            return f"{user}: Q{self.question.order} → {self.selected_choice.text[:30]}"
        return f"{user}: Q{self.question.order} → {self.free_response[:30]}"

