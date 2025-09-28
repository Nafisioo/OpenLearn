from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

def forwards_func(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    CourseOffering = apps.get_model("courses", "CourseOffering")
    Session = apps.get_model("core", "Session")
    # Semester left nullable by design to avoid forcing ambiguous mappings
    # Backfill: create an offering for each existing Course using its instructor, is_elective and students
    # Assign current session (if any) to the new offering
    try:
        current_session = Session.objects.filter(is_current=True).first()
    except Exception:
        current_session = None

    # Copy each course into a single current offering (if not already present)
    for course in Course.objects.all():
        offering = CourseOffering.objects.create(
            course_id=course.pk,
            session=current_session,
            semester=None,
            instructor_id=getattr(course, "instructor_id", None),
            is_elective=getattr(course, "is_elective", False),
        )
        # copy students from Course.students M2M if present
        try:
            students_qs = course.students.all()
            if students_qs.exists():
                offering.students.set(students_qs)
        except Exception:
            # if course.students M2M doesn't exist or some other issue, skip copying
            pass

def reverse_func(apps, schema_editor):
    CourseOffering = apps.get_model("courses", "CourseOffering")
    CourseOffering.objects.all().delete()


class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('courses', '0010_program_remove_userlessonprogress_enrollment_and_more'),
        ('core', '0005_delete_category_remove_sitefeedback_user_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseOffering',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_elective', models.BooleanField(default=False)),
                ('capacity', models.PositiveIntegerField(blank=True, null=True, help_text='Optional capacity limit for this offering')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offerings', to='courses.course')),
                ('session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='course_offerings', to='core.session')),
                ('semester', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='course_offerings', to='core.semester')),
                ('instructor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='course_offerings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.AddField(
            model_name='courseoffering',
            name='students',
            field=models.ManyToManyField(related_name='course_offerings_enrolled', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.RunPython(forwards_func, reverse_func),
    ]