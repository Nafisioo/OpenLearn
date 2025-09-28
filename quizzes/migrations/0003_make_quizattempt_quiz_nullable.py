from django.db import migrations, models
import django.db.models.deletion 

class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("quizzes", "0002_add_course_and_populate"),
    ]

    operations = [

        migrations.AlterField(
            model_name="quizattempt",
            name="quiz",
            field=models.ForeignKey(
                to="quizzes.Quiz",
                on_delete=django.db.models.CASCADE,
                related_name="attempts",
                null=True,
            ),
        ),
    ]