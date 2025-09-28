from django.db import migrations, models
from django.db.models import Q

def set_default_semester(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    # Use "fall" as a sensible default for all existing courses
    Course.objects.filter(Q(semester__isnull=True) | Q(semester="")).update(semester="fall")

class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0008_add_program_and_populate"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="semester",
            field=models.CharField(
                choices=[("fall", "Fall"), ("spring", "Spring")],
                max_length=200,
                null=True,
                blank=True,
            ),
        ),
        migrations.RunPython(set_default_semester, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="course",
            name="semester",
            field=models.CharField(
                choices=[("fall", "Fall"), ("spring", "Spring")],
                max_length=200,
                null=False,
                blank=False,
            ),
        ),
    ]