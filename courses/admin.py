from django.contrib import admin
from .models import Course, Lesson, Enrollment, UserLessonProgress

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'order')
    ordering = ['order']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'created_at')
    search_fields = ('title', 'description', 'instructor__username')
    list_filter = ('created_at',)
    inlines = [LessonInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'instructor')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    search_fields = ('title', 'course__title')
    list_filter = ('course',)
    ordering = ['course', 'order']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at')
    search_fields = ('user__username', 'course__title')
    list_filter = ('enrolled_at', 'course')

@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'lesson', 'completed')
    list_filter = ('completed', 'lesson__course')
    search_fields = ('enrollment__user__username', 'lesson__title')

    def get_user(self, obj):
        return obj.enrollment.user.username if obj.enrollment else '—'
    get_user.short_description = 'User'

