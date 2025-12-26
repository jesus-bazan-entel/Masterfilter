from django.contrib import admin

from .models import *
# Register your models here.
class DocumentAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class EndPointAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class PermisionAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class UserPangeaAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class ScrapingJobAdmin(admin.ModelAdmin):
    list_display = ["id", "file_name", "user", "status", "retry_count", "created_at", "updated_at"]
    list_filter = ["status", "created_at", "user"]
    search_fields = ["id", "file_name", "user__username"]
    readonly_fields = ["created_at", "updated_at", "started_at", "completed_at"]
    actions = ["retry_failed_jobs", "mark_as_timeout"]
    
    def retry_failed_jobs(self, request, queryset):
        """Acción para reintentar jobs fallidos"""
        count = 0
        for job in queryset:
            if job.can_retry():
                job.increment_retry()
                count += 1
        self.message_user(request, f"{count} jobs marcados para reintento")
    retry_failed_jobs.short_description = "Reintentar jobs seleccionados"
    
    def mark_as_timeout(self, request, queryset):
        """Acción para marcar jobs como timeout"""
        count = queryset.update(status='timeout')
        self.message_user(request, f"{count} jobs marcados como timeout")
    mark_as_timeout.short_description = "Marcar como timeout"

admin.site.register(Document, DocumentAdmin)
admin.site.register(EndPoint, EndPointAdmin)
admin.site.register(Permision, PermisionAdmin)
admin.site.register(UserPangea, UserPangeaAdmin)
admin.site.register(ScrapingJob, ScrapingJobAdmin)
