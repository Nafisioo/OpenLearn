from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save, post_delete, post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.models import ActivityLog, Semester
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

class CourseManager(models.Manager):
    def search(self, query=None):
        qs = self.get_queryset()
        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(summary__icontains=query) |
                Q(code__icontains=query) |
                Q(slug__icontains=query)
            ).distinct()
        return qs
    

LEVEL_CHOICES = [
    ('bachelor', 'Bachelor'),
    ('master', 'Master'),
]

YEARS = [
    (1, 'Year 1'),
    (2, 'Year 2'),
    (3, 'Year 3'),
    (4, 'Year 4'),
]

SEMESTER_CHOICES = [
    ('fall', 'Fall'),
    ('spring', 'Spring'),
]

class Course(models.Model):
    slug = models.SlugField(unique=True, blank=True)
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=200, unique=True)
    credit = models.PositiveIntegerField(default=0)
    summary = models.TextField(max_length=200, blank=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="courses")
    level = models.CharField(max_length=25, choices=LEVEL_CHOICES)
    year = models.PositiveSmallIntegerField(YEARS, default=1)
    semester = models.CharField(choices=SEMESTER_CHOICES, max_length=200)
    is_elective = models.BooleanField(default=False)

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses_taught",
    )

    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="courses_enrolled",
        blank=True,
    )

    objects = CourseManager()

    class Meta:
        ordering = ("-created_at",) if hasattr(models.Model, "created_at") else ()

    def __str__(self):
        return f"{self.title} ({self.code})"

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"slug": self.slug})


    @property
    def is_current_semester(self):
        current = Semester.objects.filter(is_current_semester=True).first()
        return self.semester == getattr(current, "semester", None)
    
    def enroll(self, user):
        if user is None:
            return
        if not self.students.filter(pk=user.pk).exists():
            self.students.add(user)

    def unenroll(self, user):
        if user is None:
            return
        if self.students.filter(pk=user.pk).exists():
            self.students.remove(user)

    def is_enrolled(self, user):
        if user is None:
            return False
        return self.students.filter(pk=user.pk).exists()

@receiver(pre_save, sender=Course)
def course_pre_save_receiver(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)

@receiver(post_save, sender=Course)
def log_course_save(sender, instance, created, **kwargs):
    verb = "created" if created else "updated"
    try:
        ActivityLog.objects.create(message=_(f"The course '{instance}' has been {verb}."))
    except Exception:
        pass

@receiver(post_delete, sender=Course)
def log_course_delete(sender, instance, **kwargs):
    try:
        ActivityLog.objects.create(message=_(f"The course '{instance}' has been deleted."))
    except Exception:
        pass

# --- COURSE ALLOCATION ---

class CourseAllocation(models.Model):
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_allocations"
    )
    courses = models.ManyToManyField(Course, related_name="allocations")
    session = models.ForeignKey("core.Session", on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        try:
            return self.lecturer.get_full_name_or_username()
        except Exception:
            return str(self.lecturer)

    def get_absolute_url(self):
        return reverse("edit_allocated_course", kwargs={"pk": self.pk})


# --- UPLOAD ---

class Upload(models.Model):
    title = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="uploads")
    file = models.FileField(
        upload_to="course_files/",
        help_text=_("Valid files: pdf, docx, doc, xls, xlsx, ppt, pptx, zip, rar, 7zip"),
        validators=[FileExtensionValidator(["pdf", "docx", "doc", "xls", "xlsx", "ppt", "pptx", "zip", "rar", "7zip"])]
    )
    updated_date = models.DateTimeField(auto_now=True)
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_extension_short(self):
        ext = self.file.name.split(".")[-1].lower()
        mapping = {
            ("doc", "docx"): "word",
            ("pdf",): "pdf",
            ("xls", "xlsx"): "excel",
            ("ppt", "pptx"): "powerpoint",
            ("zip", "rar", "7zip"): "archive",
        }
        for exts, label in mapping.items():
            if ext in exts:
                return label
        return "file"

    def delete(self, *args, **kwargs):
        self.file.delete(save=False)
        super().delete(*args, **kwargs)

@receiver(post_save, sender=Upload)
def log_upload_save(sender, instance, created, **kwargs):
    msg = (
        _(f"The file '{instance.title}' has been uploaded to the course '{instance.course}'.")
        if created else
        _(f"The file '{instance.title}' of the course '{instance.course}' has been updated.")
    )
    ActivityLog.objects.create(message=msg)

@receiver(post_delete, sender=Upload)
def log_upload_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        message=_(f"The file '{instance.title}' of the course '{instance.course}' has been deleted.")
    )


# --- UPLOAD VIDEO ---

class UploadVideo(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="videos")
    video = models.FileField(
        upload_to="course_videos/",
        help_text=_("Valid video formats: mp4, mkv, wmv, 3gp, f4v, avi, mp3"),
        validators=[FileExtensionValidator(["mp4", "mkv", "wmv", "3gp", "f4v", "avi", "mp3"])]
    )
    summary = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "video_single", kwargs={"slug": self.course.slug, "video_slug": self.slug}
        )

    def delete(self, *args, **kwargs):
        self.video.delete(save=False)
        super().delete(*args, **kwargs)

@receiver(pre_save, sender=UploadVideo)
def video_pre_save_receiver(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)

@receiver(post_save, sender=UploadVideo)
def log_uploadvideo_save(sender, instance, created, **kwargs):
    msg = (
        _(f"The video '{instance.title}' has been uploaded to the course '{instance.course}'.")
        if created else
        _(f"The video '{instance.title}' of the course '{instance.course}' has been updated.")
    )
    ActivityLog.objects.create(message=msg)

@receiver(post_delete, sender=UploadVideo)
def log_uploadvideo_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        message=_(f"The video '{instance.title}' of the course '{instance.course}' has been deleted.")
    )


# --- COURSE OFFER ---

class CourseOffer(models.Model):
    dep_head = models.ForeignKey("accounts.DepartmentHead", on_delete=models.CASCADE, related_name="course_offers")

    def __str__(self):
        return str(self.dep_head)