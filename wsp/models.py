from django.db import models

# Create your models here.
from django.db import models

class WhatsAppModule(models.Model):
    """
    Modelo proxy para gestionar permisos del módulo WhatsApp
    """
    class Meta:
        managed = False  # No crea tabla en la BD
        default_permissions = ()  # Evita permisos automáticos
        permissions = [
            ('can_access_whatsapp', 'Puede acceder al módulo WhatsApp'),
            ('can_consult_numbers', 'Puede consultar números de WhatsApp'),
            ('can_bulk_consult', 'Puede hacer consultas masivas'),
        ]
        verbose_name = 'Módulo WhatsApp'
        verbose_name_plural = 'Permisos WhatsApp'