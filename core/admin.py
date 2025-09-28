from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import NewsAndEvents, Session, Semester, ActivityLog

@admin.register(NewsAndEvents)
class NewsAndEventsAdmin(admin.ModelAdmin):
    list_display = ('title', 'posted_as', 'created_at', 'updated_at')
    list_filter = ('posted_as', 'created_at')
    search_fields = ('title', 'summary')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('title', 'summary', 'posted_as')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_current', 'next_session_begins', 'created_at')
    list_filter = ('is_current',)
    search_fields = ('name',)
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('name', 'is_current', 'next_session_begins')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if obj.is_current:
            Session.objects.filter(is_current=True).exclude(pk=obj.pk).update(is_current=False)
        super().save_model(request, obj, form, change)

@admin.register(Semester) 
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('semester', 'session', 'is_current', 'next_semester_begins', 'created_at')
    list_filter = ('is_current', 'semester', 'session')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('semester', 'session', 'is_current', 'next_semester_begins')
        }),
    )

    def save_model(self, request, obj, form, change):
        if obj.is_current and obj.session:
            Semester.objects.filter(is_current=True, session=obj.session).exclude(pk=obj.pk).update(is_current=False)
        super().save_model(request, obj, form, change)

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('truncated_message', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('message',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    def truncated_message(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    truncated_message.short_description = _('Message')