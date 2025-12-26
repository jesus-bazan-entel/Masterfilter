from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Permision(models.Model):
    movil = models.BooleanField(default=False)
    movil_individual = models.BooleanField(default=False)
    fijo = models.BooleanField(default=False)
    orange1 = models.BooleanField(default=False)
    orange2 = models.BooleanField(default=False)
    wsp = models.BooleanField(default=False)
    abct = models.BooleanField(default=True)
    amarilla = models.BooleanField(default=True)
    infobel = models.BooleanField(default=True)
    peoplecall = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)
    
class Document(models.Model):
    file = models.FileField(upload_to="subido")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.IntegerField(default=0)

class EndPoint(models.Model):
    movil = models.CharField(max_length=150)
    fijo = models.CharField(max_length=150)
    orange1 = models.CharField(max_length=150)
    orange2 = models.CharField(max_length=150)
    abct = models.CharField(max_length=150)
    wsp = models.CharField(max_length=150, null=True, blank=True)
    amarilla = models.CharField(max_length=150, null=True, blank=True)
    infobel = models.CharField(max_length=150, null=True, blank=True)

class UserPangea(models.Model):
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=150)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)

class ScrapingJob(models.Model):
    """
    Modelo para rastrear el estado de los jobs de web scraping
    y permitir reintentos automáticos
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('timeout', 'Timeout'),
        ('retrying', 'Reintentando'),
    ]
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='scraping_jobs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tracking temporal
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Reintentos
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    last_error = models.TextField(null=True, blank=True)
    
    # Datos del job
    total_numbers = models.IntegerField(default=0)
    processed_numbers = models.IntegerField(default=0)
    
    # Timeout detection (en minutos)
    timeout_minutes = models.IntegerField(default=30)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'updated_at']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"Job {self.id} - {self.file_name} ({self.status})"
    
    def is_timed_out(self):
        """Verifica si el job ha excedido el tiempo límite"""
        if self.status in ['completed', 'failed']:
            return False
        
        if self.started_at:
            elapsed = timezone.now() - self.started_at
            return elapsed.total_seconds() / 60 > self.timeout_minutes
        return False
    
    def can_retry(self):
        """Verifica si el job puede ser reintentado"""
        return self.retry_count < self.max_retries and self.status in ['failed', 'timeout']
    
    def mark_as_processing(self):
        """Marca el job como en proceso"""
        self.status = 'processing'
        if not self.started_at:
            self.started_at = timezone.now()
        self.save()
    
    def mark_as_completed(self):
        """Marca el job como completado"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message=None):
        """Marca el job como fallido"""
        self.status = 'failed'
        if error_message:
            self.last_error = error_message
        self.save()
    
    def mark_as_timeout(self):
        """Marca el job como timeout"""
        self.status = 'timeout'
        self.last_error = f"Job excedió el tiempo límite de {self.timeout_minutes} minutos"
        self.save()
    
    def increment_retry(self):
        """Incrementa el contador de reintentos"""
        self.retry_count += 1
        self.status = 'retrying'
        self.save()
