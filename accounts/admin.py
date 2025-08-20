from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from .models import Student, Parent, DepartmentHead

User = get_user_model()


class StudentInline(admin.TabularInline):
    model = Student
    can_delete = False
    verbose_name = "Student profile"
    verbose_name_plural = "Student profile"
    fk_name = "user"
    max_num = 1
    extra = 0
    fields = ("level", "program")


class ParentInline(admin.TabularInline):
    model = Parent
    can_delete = False
    verbose_name = "Parent profile"
    verbose_name_plural = "Parent profile"
    fk_name = "user"
    max_num = 1
    extra = 0
    filter_horizontal = ("students",)
    fields = ("phone", "email")


class DepartmentHeadInline(admin.TabularInline):
    model = DepartmentHead
    can_delete = False
    verbose_name = "Department head profile"
    verbose_name_plural = "Department head profile"
    fk_name = "user"
    max_num = 1
    extra = 0
    fields = ("department",)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = (StudentInline, ParentInline, DepartmentHeadInline)
    list_display = (
        "username",
        "get_full_name_or_username",
        "email",
        "role",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "phone", "picture", "role")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "role", "email"),
            },
        ),
    )

    actions = (
        "make_students",
        "make_instructors",
        "make_admins",
        "enable_users",
        "disable_users",
        "create_student_profiles",
    )

    def get_inline_instances(self, request, obj=None):
        inline_instances = []
        if obj:
            for inline in self.inlines:
                inline_instances.append(inline(self.model, self.admin_site))
        return inline_instances

    @admin.action(description="Set selected users role → Student")
    def make_students(self, request, queryset):
        with transaction.atomic():
            queryset.update(role=User.Role.STUDENT)
            created = 0
            for user in queryset:
                obj, was_created = Student.objects.get_or_create(user=user)
                if was_created:
                    created += 1
        self.message_user(request, f"Marked {queryset.count()} users as Student. Created {created} Student profile(s).")

    @admin.action(description="Set selected users role → Instructor")
    def make_instructors(self, request, queryset):
        queryset.update(role=User.Role.INSTRUCTOR)
        self.message_user(request, f"Marked {queryset.count()} users as Instructor.")

    @admin.action(description="Set selected users role → Admin (is_staff=True)")
    def make_admins(self, request, queryset):
        queryset.update(role=User.Role.ADMIN, is_staff=True)
        self.message_user(request, f"Marked {queryset.count()} users as Admin and set is_staff=True.")

    @admin.action(description="Enable selected users (is_active=True)")
    def enable_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Enabled {queryset.count()} user(s).")

    @admin.action(description="Disable selected users (is_active=False)")
    def disable_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Disabled {queryset.count()} user(s).")

    @admin.action(description="Create missing Student profiles for selected users")
    def create_student_profiles(self, request, queryset):
        created = 0
        with transaction.atomic():
            for user in queryset:
                obj, was_created = Student.objects.get_or_create(user=user)
                if was_created:
                    created += 1
        self.message_user(request, f"Created {created} missing Student profile(s).")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("user", "level", "program")
    search_fields = ("user__username", "user__first_name", "user__last_name", "program__title")
    list_filter = ("level",)
    raw_id_fields = ("user", "program")
    ordering = ("-user__date_joined",)


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "email")
    search_fields = ("user__username", "user__first_name", "user__last_name", "email", "phone")
    filter_horizontal = ("students",)
    raw_id_fields = ("user",)
    ordering = ("-user__date_joined",)


@admin.register(DepartmentHead)
class DepartmentHeadAdmin(admin.ModelAdmin):
    list_display = ("user", "department")
    search_fields = ("user__username", "user__first_name", "user__last_name", "department__title")
    raw_id_fields = ("user", "department")
