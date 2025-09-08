from django.contrib import admin
from texts.models import Text


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ('id', 'theme', 'platform')
