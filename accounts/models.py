from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

try:
    from PIL import Image
except Exception:
    Image=None
class CustomUserManager(UserManager):
    def search(self, query=None):
        qs = self.get_queryset()
        if query:
            q = (
                Q(username__icontains=query)
                | Q(first_name__icontains=query)   
                | Q(last_name__icontains=query)    
                | Q(email__icontains=query)        
            )
            qs = qs.filter(q).distinct()           
        return qs
    

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", _("Student")
        INSTRUCTOR = "instructor", _("Instructor")
        ADMIN = "admin", _("Admin")

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=40, blank=True, null=True)
    picture = models.ImageField(
        upload_to="profile_pictures/%y/%m/%d/",
        default="default.png",
        null=True,
        blank=True)
    email = models.EmailField(blank=True, null=True)


    objects = CustomUserManager()

    class Meta:
        ordering = ("-date_joined",)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_full_name_or_username(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_picture_url(self):
        try:
            return self.picture.url
        except Exception:
            return settings.MEDIA_URL + "default.png"
    
    def get_absolute_url(self):
        return reverse("accounts:profile", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)
        
        if Image is None:
            return
        if not self.picture:
            return
        try:
            if hasattr(self.picture, "path"):
                img = Image.open(self.picture.path)
                output_size = (300, 300)
                if img.height > 300 or img.width > 300:
                    img.thumbnail(output_size)
                    img.save(self.picture.path)
        except Exception:
            pass
        

BACHELOR = _("Bachelor")
MASTER = _("Master")
LEVEL_CHOICES = [
    (BACHELOR, _("Bachelor Degree")),
    (MASTER, _("Master Degree"))
    ]


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    level = models.CharField(max_length=25, choices=LEVEL_CHOICES,blank=True, null=True)
    program = models.ForeignKey("courses.Course", null=True, blank=True, on_delete=models.SET_NULL, related_name="students_profiles")

    class Meta:
        ordering = ("-user__date_joined",)

    def __str__(self):
        return self.user.get_full_name_or_username()
    
    def get_absolute_url(self):
        return reverse("accounts:student_profile", kwargs={"pk": self.pk})

    
class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")
    students = models.ManyToManyField(Student, related_name="parents", blank= True)
    phone = models.CharField(max_length=60, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        ordering = ("-user__date_joined",)

    def __str__(self):
        return f"Parent: {self.user.get_full_name_or_username()}"


class DepartmentHead(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="dept_head_profile")
    department = models.ForeignKey("courses.Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="department_heads")

    def __str__(self):
        return str(self.user)