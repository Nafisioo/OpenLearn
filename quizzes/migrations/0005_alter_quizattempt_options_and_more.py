import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0004_populate_quizattempt_quiz_and_make_nonnull'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='quizattempt',
            options={'ordering': ['-started_at']},
        ),
        migrations.AlterUniqueTogether(
            name='quizattempt',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='quiz',
            name='lesson',
        ),
        migrations.AddField(
            model_name='quiz',
            name='draft',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='quiz',
            name='pass_mark',
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name='quiz',
            name='random_order',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='quiz',
            name='single_attempt',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='attempt_number',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quiz_attempts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='answer',
            name='free_response',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='answer',
            name='selected_choice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='quizzes.choice'),
        ),
        migrations.AlterField(
            model_name='question',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='quizattempt',
            name='score',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Percentage score 0.00 - 100.00', max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='quizattempt',
            name='started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name='quizattempt',
            index=models.Index(fields=['quiz', 'user'], name='qa_quiz_user_idx'),
        ),
        migrations.RemoveField(
            model_name='quizattempt',
            name='enrollment',
        ),
    ]