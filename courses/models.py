from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.models import ActivityLog, Semester, Session
from core.utils import unique_slug_generator


# --- PROGRAM ---
class ProgramManager(models.Manager):
    def search(self, query=None):
        qs = self.get_queryset()
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(summary__icontains=query)).distinct()
        return qs


class Program(models.Model):
    title = models.CharField(max_length=150, unique=True)
    summary = models.TextField(blank=True)
    objects = ProgramManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("program_detail", kwargs={"pk": self.pk})


@receiver(post_save, sender=Program)
def log_program_save(sender, instance, created, **kwargs):
    verb = "created" if created else "updated"
    ActivityLog.objects.create(message=_(f"The program '{instance}' has been {verb}."))


@receiver(post_delete, sender=Program)
def log_program_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(message=_(f"The program '{instance}' has been deleted."))


# --- COURSE ---
LEVEL_CHOICES = [
    ("bachelor", "Bachelor"),
    ("master", "Master"),
]

YEARS = [(1, "Year 1"), (2, "Year 2"), (3, "Year 3"), (4, "Year 4")]
SEMESTER_CHOICES = [("fall", "Fall"), ("spring", "Spring")]


class CourseManager(models.Manager):
    def search(self, query=None):
        qs = self.get_queryset()
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(code__icontains=query)
                | Q(slug__icontains=query)
            ).distinct()
        return qs


class Course(models.Model):
    slug = models.SlugField(unique=True, blank=True)
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=200, unique=True)
    credit = models.PositiveIntegerField(default=0)
    summary = models.TextField(max_length=200, blank=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="courses")
    level = models.CharField(max_length=25, choices=LEVEL_CHOICES)
    year = models.PositiveSmallIntegerField(choices=YEARS, default=1)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    is_elective = models.BooleanField(default=False)

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses_taught"
    )

    objects = CourseManager()

    class Meta:
        ordering = ("-id",)

    def __str__(self):
        return f"{self.title} ({self.code})"

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"slug": self.slug})


@receiver(pre_save, sender=Course)
def course_pre_save(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)


@receiver(post_save, sender=Course)
def log_course_save(sender, instance, created, **kwargs):
    verb = "created" if created else "updated"
    ActivityLog.objects.create(message=_(f"The course '{instance}' has been {verb}."))


@receiver(post_delete, sender=Course)
def log_course_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(message=_(f"The course '{instance}' has been deleted."))


# --- COURSE OFFERING ---
class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="offerings")
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, related_name="course_offerings")
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True, related_name="course_offerings")
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="course_offerings")
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="course_offerings_enrolled", blank=True)
    is_elective = models.BooleanField(default=False)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["session", "semester"]), models.Index(fields=["course"])]

    def __str__(self):
        session_label = str(self.session) if self.session else "NoSession"
        semester_label = str(self.semester) if self.semester else "NoSemester"
        return f"{self.course} — {session_label}/{semester_label}"

    def enroll(self, user):
        if user and (self.capacity is None or self.students.count() < self.capacity):
            self.students.add(user)

    def unenroll(self, user):
        if user:
            self.students.remove(user)

    def is_enrolled(self, user):
        return user and self.students.filter(pk=user.pk).exists()


# --- COURSE ALLOCATION ---
class CourseAllocation(models.Model):
    lecturer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_allocations")
    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="allocations")

    def __str__(self):
        return self.lecturer.get_full_name_or_username()

    def get_absolute_url(self):
        return reverse("edit_allocated_course", kwargs={"pk": self.pk})


# --- COURSE RESOURCES (FILES & VIDEOS MERGED) ---
RESOURCE_TYPES = [("file", "File"), ("video", "Video")]


class Resource(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="resources")
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES, default="file")
    file = models.FileField(upload_to="course_resources/")
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("resource_detail", kwargs={"course_slug": self.course.slug, "slug": self.slug})

    def delete(self, *args, **kwargs):
        self.file.delete(save=False)
        super().delete(*args, **kwargs)


@receiver(pre_save, sender=Resource)
def resource_pre_save(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)


@receiver(post_save, sender=Resource)
def log_resource_save(sender, instance, created, **kwargs):
    verb = "uploaded" if created else "updated"
    ActivityLog.objects.create(
        message=_(f"The {instance.resource_type} '{instance.title}' has been {verb} to course '{instance.course}'.")
    )


@receiver(post_delete, sender=Resource)
def log_resource_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        message=_(f"The {instance.resource_type} '{instance.title}' of course '{instance.course}' has been deleted.")
    )
