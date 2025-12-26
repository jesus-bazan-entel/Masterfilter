"""
Comando de management para verificar y reintentar jobs de scraping
que están en timeout o fallidos.

Uso:
    python manage.py check_scraping_jobs
    python manage.py check_scraping_jobs --retry-failed
    python manage.py check_scraping_jobs --timeout-minutes 45
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from movil.models import ScrapingJob
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verifica jobs de scraping en timeout y reintenta jobs fallidos automáticamente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--retry-failed',
            action='store_true',
            help='Reintenta automáticamente jobs fallidos',
        )
        parser.add_argument(
            '--timeout-minutes',
            type=int,
            default=30,
            help='Minutos para considerar un job como timeout (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la ejecución sin hacer cambios',
        )

    def handle(self, *args, **options):
        retry_failed = options['retry_failed']
        timeout_minutes = options['timeout_minutes']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Verificando jobs de scraping...'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # 1. Detectar jobs en timeout
        self.check_timeout_jobs(timeout_minutes, dry_run)

        # 2. Reintentar jobs fallidos si está habilitado
        if retry_failed:
            self.retry_failed_jobs(dry_run)

        # 3. Mostrar estadísticas
        self.show_statistics()

        self.stdout.write(self.style.SUCCESS('\n✓ Verificación completada'))

    def check_timeout_jobs(self, timeout_minutes, dry_run):
        """Detecta y marca jobs que están en timeout"""
        self.stdout.write(self.style.WARNING(f'\n1. Verificando jobs en timeout (>{timeout_minutes} min)...'))
        
        # Buscar jobs en procesamiento que pueden estar en timeout
        processing_jobs = ScrapingJob.objects.filter(
            status__in=['processing', 'pending', 'retrying']
        )

        timeout_count = 0
        for job in processing_jobs:
            if job.is_timed_out():
                timeout_count += 1
                elapsed = (timezone.now() - job.started_at).total_seconds() / 60 if job.started_at else 0
                
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ Job #{job.id} ({job.file_name}) - '
                        f'Usuario: {job.user.username} - '
                        f'Tiempo transcurrido: {elapsed:.1f} min'
                    )
                )
                
                if not dry_run:
                    job.mark_as_timeout()
                    self.stdout.write(self.style.ERROR('    → Marcado como TIMEOUT'))

        if timeout_count == 0:
            self.stdout.write(self.style.SUCCESS('  ✓ No se encontraron jobs en timeout'))
        elif dry_run:
            self.stdout.write(self.style.WARNING(f'  → {timeout_count} jobs serían marcados como timeout (DRY RUN)'))
        else:
            self.stdout.write(self.style.ERROR(f'  → {timeout_count} jobs marcados como timeout'))

    def retry_failed_jobs(self, dry_run):
        """Reintenta jobs fallidos que aún tienen reintentos disponibles"""
        self.stdout.write(self.style.WARNING('\n2. Reintentando jobs fallidos...'))
        
        failed_jobs = ScrapingJob.objects.filter(
            status__in=['failed', 'timeout']
        )

        retry_count = 0
        max_retries_count = 0

        for job in failed_jobs:
            if job.can_retry():
                retry_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'  🔄 Job #{job.id} ({job.file_name}) - '
                        f'Usuario: {job.user.username} - '
                        f'Reintento {job.retry_count + 1}/{job.max_retries}'
                    )
                )
                
                if not dry_run:
                    job.increment_retry()
                    # Aquí se puede agregar lógica para reenviar el job
                    from movil.views import send_data, read_file
                    try:
                        data = read_file(job.file_name)
                        if data:
                            send_data(job.user.username, data, False, job.file_name)
                            self.stdout.write(self.style.SUCCESS('    → Job reenviado exitosamente'))
                        else:
                            job.mark_as_failed("Error al leer archivo para reintento")
                            self.stdout.write(self.style.ERROR('    → Error al leer archivo'))
                    except Exception as e:
                        job.mark_as_failed(str(e))
                        self.stdout.write(self.style.ERROR(f'    → Error: {str(e)}'))
            else:
                max_retries_count += 1

        if retry_count == 0 and max_retries_count == 0:
            self.stdout.write(self.style.SUCCESS('  ✓ No hay jobs para reintentar'))
        else:
            if retry_count > 0:
                if dry_run:
                    self.stdout.write(self.style.WARNING(f'  → {retry_count} jobs serían reintentados (DRY RUN)'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {retry_count} jobs reintentados'))
            
            if max_retries_count > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ⚠ {max_retries_count} jobs alcanzaron el máximo de reintentos'
                    )
                )

    def show_statistics(self):
        """Muestra estadísticas generales de los jobs"""
        self.stdout.write(self.style.WARNING('\n3. Estadísticas generales:'))
        
        stats = {
            'pending': ScrapingJob.objects.filter(status='pending').count(),
            'processing': ScrapingJob.objects.filter(status='processing').count(),
            'completed': ScrapingJob.objects.filter(status='completed').count(),
            'failed': ScrapingJob.objects.filter(status='failed').count(),
            'timeout': ScrapingJob.objects.filter(status='timeout').count(),
            'retrying': ScrapingJob.objects.filter(status='retrying').count(),
        }

        self.stdout.write(f'  📊 Pendientes:   {stats["pending"]}')
        self.stdout.write(f'  ⚙️  Procesando:   {stats["processing"]}')
        self.stdout.write(f'  ✅ Completados:  {stats["completed"]}')
        self.stdout.write(f'  ❌ Fallidos:     {stats["failed"]}')
        self.stdout.write(f'  ⏱️  Timeout:      {stats["timeout"]}')
        self.stdout.write(f'  🔄 Reintentando: {stats["retrying"]}')
        self.stdout.write(f'  ━━━━━━━━━━━━━━━━━━━━')
        self.stdout.write(f'  📈 Total:        {sum(stats.values())}')
