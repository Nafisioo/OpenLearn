from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Course, CourseAllocation


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "code",
        "program",
        "level",
        "year",
        "semester",
        "instructor",
        "is_elective",
    )
    search_fields = (
        "title",
        "summary",
        "code",
        "slug",
        "instructor__username",
        "program__title",
    )
    list_filter = ("program", "level", "year", "semester", "is_elective")
    ordering = ("title",)
    autocomplete_fields = ("instructor",)
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {
            "fields": (
                "slug",
                "title",
                "code",
                "program",
                "level",
                "year",
                "semester",
                "credit",
                "is_elective",
                "instructor",
                "summary",
            )
        }),
        (_("Allocation & Metadata"), {
            "fields": (),
            "classes": ("collapse",),
        }),
    )


@admin.register(CourseAllocation)
class CourseAllocationAdmin(admin.ModelAdmin):
    list_display = ("lecturer", "offering")
    search_fields = ("lecturer__username", "offering__course__title")
    list_filter = ("offering__session", "offering__semester")  
    autocomplete_fields = ("lecturer",)