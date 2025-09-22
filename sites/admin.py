from django.contrib import admin
from sites.models import Site


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'url', 'monitored', 'enable_recursive_crawling', 'created_at')
    list_filter = ('monitored', 'enable_recursive_crawling', 'category', 'created_at')
    list_editable = ('monitored', 'enable_recursive_crawling')
    search_fields = ('name', 'url', 'category')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'url', 'category')
        }),
        ('Configurações de Monitoramento', {
            'fields': ('monitored', 'enable_recursive_crawling'),
            'description': 'Monitored = True: Replica posts automaticamente. False = Apenas webscraping recursivo.'
        }),
        ('Configurações de Crawling', {
            'fields': ('max_depth', 'max_pages', 'allow_patterns', 'deny_patterns', 'content_selectors'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
