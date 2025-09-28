from django.db import migrations, models
import django.db.models.deletion

def populate_quiz_for_attempts(apps, schema_editor):
    QuizAttempt = apps.get_model("quizzes", "QuizAttempt")
    Quiz = apps.get_model("quizzes", "Quiz")
    Course = apps.get_model("courses", "Course")

    default_quiz = Quiz.objects.first()

    if default_quiz is None:
        first_course = Course.objects.first()
        if first_course is None:
            raise RuntimeError(
                "Migration requires at least one Quiz or one Course in the database. "
                "Please create a Course (and optionally a Quiz) before running migrations."
            )
        default_quiz = Quiz.objects.create(
            course_id=first_course.pk,
            title="Placeholder Quiz (migration)",
            description="Automatically created placeholder quiz to satisfy non-null constraint during migration.",
            random_order=False,
            single_attempt=False,
            pass_mark=50,
            draft=True,
        )

    QuizAttempt.objects.filter(quiz__isnull=True).update(quiz_id=default_quiz.pk)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("quizzes", "0003_make_quizattempt_quiz_nullable"),
    ]

    operations = [
        migrations.RunPython(populate_quiz_for_attempts, reverse_code=migrations.RunPython.noop),

        migrations.AlterField(
            model_name="quizattempt",
            name="quiz",
            field=models.ForeignKey(
                to="quizzes.Quiz",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attempts",
                null=False,
            ),
        ),
    ]