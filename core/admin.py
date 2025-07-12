from django.contrib import admin
from .models import Category, SiteFeedback


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    ordering = ['name']


@admin.register(SiteFeedback)
class SiteFeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_snippet', 'is_reviewed', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'message')

    def is_reviewed(self, obj):
        return obj.rating is not None
    is_reviewed.boolean = True
    is_reviewed.short_description = 'Reviewed'

    def message_snippet(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_snippet.short_description = 'Message'

