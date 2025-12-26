"""
Comando simplificado para ser ejecutado por cron.
Verifica y reintenta jobs automáticamente.

Uso en crontab:
    # Ejecutar cada 15 minutos
    */15 * * * * cd /opt/masterfilter && python manage.py auto_retry_jobs >> /var/log/scraping_jobs.log 2>&1
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from movil.models import ScrapingJob
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Comando automático para verificar y reintentar jobs de scraping'

    def handle(self, *args, **options):
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{timestamp}] Iniciando verificación automática de jobs...")
        
        # Detectar timeouts
        timeout_count = self.check_timeouts()
        
        # Reintentar fallidos
        retry_count = self.retry_failed()
        
        print(f"[{timestamp}] Verificación completada: {timeout_count} timeouts, {retry_count} reintentos")
        
    def check_timeouts(self):
        """Detecta y marca jobs en timeout"""
        processing_jobs = ScrapingJob.objects.filter(
            status__in=['processing', 'pending', 'retrying']
        )
        
        count = 0
        for job in processing_jobs:
            if job.is_timed_out():
                print(f"  ⚠ Timeout detectado: Job #{job.id} - {job.file_name}")
                job.mark_as_timeout()
                count += 1
        
        return count
    
    def retry_failed(self):
        """Reintenta jobs fallidos"""
        failed_jobs = ScrapingJob.objects.filter(
            status__in=['failed', 'timeout']
        )
        
        count = 0
        for job in failed_jobs:
            if job.can_retry():
                print(f"  🔄 Reintentando: Job #{job.id} - {job.file_name} (intento {job.retry_count + 1}/{job.max_retries})")
                job.increment_retry()
                
                # Reintentar el job
                from movil.views import send_data, read_file
                try:
                    data = read_file(job.file_name)
                    if data:
                        send_data(job.user.username, data, False, job.file_name, job)
                        print(f"    ✓ Job reenviado exitosamente")
                        count += 1
                    else:
                        job.mark_as_failed("Error al leer archivo para reintento")
                        print(f"    ✗ Error al leer archivo")
                except Exception as e:
                    job.mark_as_failed(str(e))
                    print(f"    ✗ Error: {str(e)}")
        
        return count
