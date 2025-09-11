from django.contrib import admin
from embeddings.models import Embedding


@admin.register(Embedding)
class EmbeddingAdmin(admin.ModelAdmin):
    list_display = ('id', 'origin', 'title', 'created_at')
    list_filter = ('origin', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ['-created_at']