from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import WhatsAppModule

@admin.register(WhatsAppModule)
class WhatsAppModuleAdmin(admin.ModelAdmin):
    """
    Admin para gestionar permisos del módulo WhatsApp
    """
    list_display = ['get_module_name', 'get_permissions_count']
    
    def get_module_name(self, obj):
        return "Módulo WhatsApp"
    get_module_name.short_description = "Módulo"
    
    def get_permissions_count(self, obj):
        content_type = ContentType.objects.get_for_model(WhatsAppModule)
        perms = Permission.objects.filter(content_type=content_type).count()
        return f"{perms} permisos disponibles"
    get_permissions_count.short_description = "Permisos"
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False