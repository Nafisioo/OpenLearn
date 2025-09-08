from django.db import models, transaction
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _



class PostType(models.TextChoices):
    NEWS = "news", _("News")
    EVENT = "event", _("Event")


class SemesterChoice(models.TextChoices):
    FIRST = "first", _("First")
    SECOND = "second", _("Second")
    THIRD = "third", _("Third")


class NewsAndEventsQuerySet(models.QuerySet):
    def search(self, query: str | None):
        if not query:
            return self
        lookups = (
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(posted_as__icontains=query)
        )
        return self.filter(lookups).distinct()
    

class NewsAndEventsManager(models.Manager):
    def get_queryset(self):
        return NewsAndEventsQuerySet(self.model, using=self._db)

    def search(self, query: str | None):
        return self.get_queryset().search(query)

    def get_by_id(self, pk: int):
        return self.get_queryset().filter(pk=pk).first()
    

class NewsAndEvents(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField(max_length=200, blank=True)
    posted_as = models.CharField(max_length=10, choices=PostType.choices, default=PostType.NEWS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = NewsAndEventsManager()

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["posted_as"]),
            models.Index(fields=["-created_at"]),
        ]
        verbose_name = _("News / Event")
        verbose_name_plural = _("News / Events")

    def __str__(self) -> str:
        return self.title or f"NewsAndEvents {self.pk}"
    

class Session(models.Model):
    name = models.CharField(max_length=200, unique=True)  
    is_current = models.BooleanField(default=False)
    next_session_begins = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["is_current"]), models.Index(fields=["name"])]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_current:
                self.__class__.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_current(cls):
        return cls.objects.filter(is_current=True).first()
    

class Semester(models.Model):
    semester = models.CharField(max_length=10, choices=SemesterChoice.choices)
    is_current = models.BooleanField(default=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="semesters", null=True, blank=True)
    next_semester_begins = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["semester"]),
            models.Index(fields=["is_current"]),
            models.Index(fields=["session"]),
        ]
        verbose_name = _("Semester")
        verbose_name_plural = _("Semesters")

    def __str__(self) -> str:
        return str(self.semester)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_current and self.session_id:
                q = self.__class__.objects.filter(is_current=True, session=self.session).exclude(pk=self.pk)
                q.update(is_current=False)
            elif self.is_current and not self.session_id:
                q = self.__class__.objects.filter(is_current=True, session__isnull=True).exclude(pk=self.pk)
                q.update(is_current=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_current(cls):
        return cls.objects.filter(is_current=True).first()


class ActivityLog(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["-created_at"])]

    def __str__(self) -> str:
        ts = timezone.localtime(self.created_at).strftime("%Y-%m-%d %H:%M:%S") if self.created_at else ""
        return f"[{ts}] {self.message[:200]}"

