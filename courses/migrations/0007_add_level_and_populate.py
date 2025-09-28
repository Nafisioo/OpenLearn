from django.db import migrations, models
from django.db.models import Q

def set_default_level(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    # Set 'bachelor' for any existing rows that don't have a level
    Course.objects.filter(Q(level__isnull=True) | Q(level="")).update(level="bachelor")


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0006_add_code_and_populate"),
    ]

    operations = [
        # 1) Add the `level` field as nullable so existing rows can accept it
        migrations.AddField(
            model_name="course",
            name="level",
            field=models.CharField(
                max_length=25,
                choices=[("bachelor", "Bachelor"), ("master", "Master")],
                null=True,
                blank=True,
            ),
        ),
        # 2) Populate existing rows with a sensible default
        migrations.RunPython(set_default_level, reverse_code=migrations.RunPython.noop),
        # 3) Make the field non-nullable to match your models.py
        migrations.AlterField(
            model_name="course",
            name="level",
            field=models.CharField(
                max_length=25,
                choices=[("bachelor", "Bachelor"), ("master", "Master")],
                null=False,
                blank=False,
            ),
        ),
    ]