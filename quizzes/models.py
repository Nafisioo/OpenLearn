from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

USER_MODEL = settings.AUTH_USER_MODEL

# --- QUIZZES ---
class Quiz(models.Model):
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    random_order = models.BooleanField(default=False)
    single_attempt = models.BooleanField(default=False)
    pass_mark = models.PositiveSmallIntegerField(default=50)
    draft = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({getattr(self.course, 'title', 'No course')})"

    def clean(self):
        if not (0 <= self.pass_mark <= 100):
            raise ValidationError("pass_mark must be between 0 and 100")

    def max_score(self):
        return self.questions.filter(type=Question.MULTIPLE_CHOICE).count()

    def user_attempts(self, user):
        return self.attempts.filter(user=user)

    def user_has_completed_attempt(self, user):
        return self.user_attempts(user).filter(completed_at__isnull=False).exists()

    def allow_new_attempt_for_user(self, user):
        if not self.single_attempt:
            return True
        return not self.user_has_completed_attempt(user)


# --- QUESTIONS & CHOICES ---
class Question(models.Model):
    MULTIPLE_CHOICE = "mcq"
    ANATOMICAL = "anat"

    QUESTION_TYPES = [
        (MULTIPLE_CHOICE, "Multiple Choice"),
        (ANATOMICAL, "Anatomical / Free Response"),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    order = models.PositiveIntegerField(default=0, db_index=True)
    type = models.CharField(max_length=4, choices=QUESTION_TYPES, default=MULTIPLE_CHOICE)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Q{self.order}: {self.text[:80]}"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return ("✔ " if self.is_correct else "✘ ") + self.text


# --- QUIZ ATTEMPTS ---
class QuizAttemptManager(models.Manager):
    def start_attempt(self, user, quiz):
        if not quiz.allow_new_attempt_for_user(user):
            raise ValidationError("User is not allowed another attempt for this quiz.")
        attempts_count = self.filter(user=user, quiz=quiz).count()
        attempt_number = attempts_count + 1
        attempt = self.create(
            user=user,
            quiz=quiz,
            attempt_number=attempt_number,
            started_at=timezone.now(),
        )



class QuizAttempt(models.Model):
    user = models.ForeignKey(USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="quiz_attempts")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    attempt_number = models.PositiveIntegerField(default=1)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                help_text="Percentage score 0.00 - 100.00")

    objects = QuizAttemptManager()

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["quiz", "user"], name="qa_quiz_user_idx"),
        ]
        unique_together = ("quiz", "user", "attempt_number")
    def __str__(self):
        username = getattr(self.user, "username", "Unknown")
        return f"{username} — {self.quiz.title} (attempt {self.attempt_number})"

    def _mcq_questions(self):
        return self.quiz.questions.filter(type=Question.MULTIPLE_CHOICE).prefetch_related("choices")


# --- ANSWERS ---
class Answer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="+"
    )
    free_response = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("attempt", "question")

    def clean(self):
        if self.question.type == Question.MULTIPLE_CHOICE:
            if self.selected_choice is None:
                raise ValidationError("Must select one of the MCQ choices.")
            if self.selected_choice.question_id != self.question_id:
                raise ValidationError("Selected choice does not belong to this question.")
        else:
            if not self.free_response:
                raise ValidationError("Must provide a free-form/anatomical response.")

    def __str__(self):
        user = getattr(self.attempt.user, "username", "UnknownUser")
        if self.question.type == Question.MULTIPLE_CHOICE and self.selected_choice:
            return f"{user}: Q{self.question.order} → {self.selected_choice.text[:40]}"
        return f"{user}: Q{self.question.order} → {self.free_response[:40]}"