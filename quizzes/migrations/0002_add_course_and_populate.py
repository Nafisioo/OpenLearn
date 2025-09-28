from django.db import migrations, models
from django.db.models import Q
from django.conf import settings

def set_course_for_existing_quizzes(apps, schema_editor):
    Quiz = apps.get_model("quizzes", "Quiz")
    Course = apps.get_model("courses", "Course")

    first_course = Course.objects.first()
    if first_course is None:
        # Fail fast with a clear message. Creating a Course automatically in this migration
        # is risky because Course has many required fields (program, instructor, etc.).
        raise RuntimeError(
            "No Course found in the database. Please create at least one Course before running this migration, "
            "so quizzes can be assigned to an existing course. Alternatively, create a Course row manually in the DB "
            "or adjust this migration to create a Course programmatically."
        )

    # Assign the first course to all existing quizzes that lack a course
    Quiz.objects.filter(Q(course__isnull=True)).update(course_id=first_course.pk)


class Migration(migrations.Migration):

    dependencies = [
        ("quizzes", "0001_initial"),
    ]

    operations = [
        # 1) Add the field as nullable so DB can accept it
        migrations.AddField(
            model_name="quiz",
            name="course",
            field=models.ForeignKey(
                to="courses.Course",
                on_delete=models.CASCADE,
                related_name="quizzes",
                null=True,
                blank=True,
            ),
        ),
        # 2) Populate existing Quiz rows with a sensible Course reference
        migrations.RunPython(set_course_for_existing_quizzes, reverse_code=migrations.RunPython.noop),
        # 3) Make the FK non-nullable to match your models.py
        migrations.AlterField(
            model_name="quiz",
            name="course",
            field=models.ForeignKey(
                to="courses.Course",
                on_delete=models.CASCADE,
                related_name="quizzes",
                null=False,
                blank=False,
            ),
        ),
    ]