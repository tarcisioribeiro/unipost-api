from django.contrib import admin
from .models import GeneratedImage


@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'embedding',
        'image_path',
        'created_at'
    ]
    list_filter = [
        'created_at',
        'updated_at'
    ]
    search_fields = [
        'original_text',
        'generated_prompt',
        'image_path'
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at'
    ]
    ordering = ['-created_at']
