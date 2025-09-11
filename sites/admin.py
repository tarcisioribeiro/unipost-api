from django.contrib import admin
from sites.models import Site


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'url')
