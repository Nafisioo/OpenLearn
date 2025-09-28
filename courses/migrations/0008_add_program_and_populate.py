from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q

def set_program_for_existing_courses(apps, schema_editor):
    Program = apps.get_model("courses", "Program")
    Course = apps.get_model("courses", "Course")

    # Use an existing program if one exists, otherwise create a default one.
    program = Program.objects.first()
    if program is None:
        program = Program.objects.create(
            title="Default Program",
            summary="Auto-created default program for migration"
        )

    # Update existing Course rows to reference the chosen program.
    Course.objects.filter(Q(program__isnull=True)).update(program_id=program.pk)


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0007_add_level_and_populate"),
    ]

    operations = [
        # 1) Add the field as nullable so the DB can accept it for existing rows
        migrations.AddField(
            model_name="course",
            name="program",
            field=models.ForeignKey(
                to="courses.Program",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="courses",
                null=True,
                blank=True,
            ),
        ),
        # 2) Populate existing rows with a sensible Program
        migrations.RunPython(set_program_for_existing_courses, reverse_code=migrations.RunPython.noop),
        # 3) Make the field non-nullable to match your models.py
        migrations.AlterField(
            model_name="course",
            name="program",
            field=models.ForeignKey(
                to="courses.Program",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="courses",
                null=False,
                blank=False,
            ),
        ),
    ]