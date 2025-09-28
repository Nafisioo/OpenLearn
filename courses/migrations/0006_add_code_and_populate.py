from django.db import migrations, models
import uuid
from django.db.models import Q

def generate_codes(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    # Populate only rows that currently have no code or empty string
    qs = Course.objects.filter(Q(code__isnull=True) | Q(code=""))
    for c in qs:
        # generate a short unique code (8 hex chars); loop until unique
        code = uuid.uuid4().hex[:8]
        while Course.objects.filter(code=code).exists():
            code = uuid.uuid4().hex[:8]
        # use queryset update() to avoid triggering model save signals
        Course.objects.filter(pk=c.pk).update(code=code)


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0005_remove_course_enrollments_course_students_and_more"),
    ]

    operations = [
        # 1) Add the field as nullable so the DB can accept it for existing rows
        migrations.AddField(
            model_name="course",
            name="code",
            field=models.CharField(max_length=200, unique=True, null=True, blank=True),
        ),
        # 2) Populate existing rows with unique values
        migrations.RunPython(generate_codes, reverse_code=migrations.RunPython.noop),
        # 3) Make the column non-nullable (final state matches your model)
        migrations.AlterField(
            model_name="course",
            name="code",
            field=models.CharField(max_length=200, unique=True, null=False),
        ),
    ]