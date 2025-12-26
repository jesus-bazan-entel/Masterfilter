# Sistema de Reintentos Automáticos para Web Scraping

## 📋 Descripción General

Sistema implementado para rastrear, monitorear y reintentar automáticamente los jobs de web scraping que no completan su procesamiento debido a timeouts, errores de red o fallos en la API externa.

## 🎯 Características Principales

### 1. **Tracking Completo de Jobs**
- Cada job de scraping es registrado en la base de datos con el modelo `ScrapingJob`
- Estados: `pending`, `processing`, `completed`, `failed`, `timeout`, `retrying`
- Información temporal: fecha de creación, inicio, actualización y completado
- Métricas: total de números, números procesados, intentos realizados

### 2. **Detección Automática de Timeouts**
- Tiempo límite configurable (default: 30 minutos)
- Verificación automática de jobs que exceden el tiempo límite
- Marcado automático como `timeout`

### 3. **Sistema de Reintentos Inteligente**
- Máximo de 3 reintentos por job (configurable)
- Reintentos automáticos para jobs con estado `failed` o `timeout`
- Registro de errores para diagnóstico

### 4. **Monitoreo y Gestión**
- Comando de management interactivo: `check_scraping_jobs`
- Comando automático para cron: `auto_retry_jobs`
- Panel de administración de Django integrado

## 🛠️ Modelo de Datos

### ScrapingJob

```python
class ScrapingJob(models.Model):
    # Relaciones
    document = ForeignKey(Document)
    user = ForeignKey(User)
    
    # Información básica
    file_name = CharField(max_length=255)
    status = CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    started_at = DateTimeField(null=True, blank=True)
    completed_at = DateTimeField(null=True, blank=True)
    
    # Reintentos
    retry_count = IntegerField(default=0)
    max_retries = IntegerField(default=3)
    last_error = TextField(null=True, blank=True)
    
    # Métricas
    total_numbers = IntegerField(default=0)
    processed_numbers = IntegerField(default=0)
    timeout_minutes = IntegerField(default=30)
```

### Métodos Principales

- `is_timed_out()`: Verifica si el job excedió el tiempo límite
- `can_retry()`: Verifica si el job puede ser reintentado
- `mark_as_processing()`: Marca el job como en proceso
- `mark_as_completed()`: Marca el job como completado
- `mark_as_failed(error)`: Marca el job como fallido con mensaje de error
- `mark_as_timeout()`: Marca el job como timeout
- `increment_retry()`: Incrementa el contador de reintentos

## 📝 Comandos de Management

### 1. check_scraping_jobs (Comando Interactivo)

Comando completo para verificación y gestión manual de jobs.

**Uso básico:**
```bash
cd /opt/masterfilter
python manage.py check_scraping_jobs
```

**Opciones:**
```bash
# Reintentar jobs fallidos automáticamente
python manage.py check_scraping_jobs --retry-failed

# Configurar tiempo de timeout personalizado (minutos)
python manage.py check_scraping_jobs --timeout-minutes 45

# Simular sin hacer cambios (dry run)
python manage.py check_scraping_jobs --dry-run --retry-failed

# Combinación de opciones
python manage.py check_scraping_jobs --retry-failed --timeout-minutes 60
```

**Salida:**
```
======================================================================
Verificando jobs de scraping...
======================================================================

1. Verificando jobs en timeout (>30 min)...
  ⚠ Job #123 (archivo.xlsx) - Usuario: user1 - Tiempo transcurrido: 45.3 min
    → Marcado como TIMEOUT
  → 1 jobs marcados como timeout

2. Reintentando jobs fallidos...
  🔄 Job #120 (datos.xlsx) - Usuario: user2 - Reintento 1/3
    → Job reenviado exitosamente
  ✓ 1 jobs reintentados

3. Estadísticas generales:
  📊 Pendientes:   2
  ⚙️  Procesando:   5
  ✅ Completados:  150
  ❌ Fallidos:     3
  ⏱️  Timeout:      1
  🔄 Reintentando: 1
  ━━━━━━━━━━━━━━━━━━━━
  📈 Total:        162

✓ Verificación completada
```

### 2. auto_retry_jobs (Comando para Cron)

Comando simplificado para ejecución automática por cron.

**Uso:**
```bash
cd /opt/masterfilter
python manage.py auto_retry_jobs
```

**Configuración en Crontab:**

```bash
# Editar crontab
crontab -e

# Agregar línea para ejecutar cada 15 minutos
*/15 * * * * cd /opt/masterfilter && python manage.py auto_retry_jobs >> /var/log/scraping_jobs.log 2>&1

# O cada 30 minutos
*/30 * * * * cd /opt/masterfilter && python manage.py auto_retry_jobs >> /var/log/scraping_jobs.log 2>&1

# O cada hora
0 * * * * cd /opt/masterfilter && python manage.py auto_retry_jobs >> /var/log/scraping_jobs.log 2>&1
```

**Salida (en log):**
```
[2025-12-23 14:30:00] Iniciando verificación automática de jobs...
  ⚠ Timeout detectado: Job #125 - clientes.xlsx
  🔄 Reintentando: Job #120 - datos.xlsx (intento 1/3)
    ✓ Job reenviado exitosamente
[2025-12-23 14:30:15] Verificación completada: 1 timeouts, 1 reintentos
```

## 🎛️ Panel de Administración Django

El modelo `ScrapingJob` está registrado en el admin de Django con funcionalidades adicionales:

**URL:** `/admin/movil/scrapingjob/`

**Características:**
- Lista de jobs con filtros por estado, fecha y usuario
- Búsqueda por ID, nombre de archivo o usuario
- Acciones en lote:
  - "Reintentar jobs seleccionados"
  - "Marcar como timeout"
- Campos de solo lectura para timestamps

**Filtros disponibles:**
- Estado (pending, processing, completed, failed, timeout, retrying)
- Fecha de creación
- Usuario

## 🔄 Flujo de Procesamiento

### Subida de Archivo (Normal)

```
1. Usuario sube archivo Excel
2. Se crea Document en BD
3. Se valida archivo (< 5000 registros)
4. Se crea ScrapingJob con status='pending'
5. ScrapingJob.mark_as_processing()
6. send_data() envía a API externa
7. Usuario exporta resultados
8. ScrapingJob.mark_as_completed()
```

### Detección y Reintento de Timeout

```
1. Comando cron ejecuta auto_retry_jobs
2. Busca jobs con status='processing' y tiempo > 30 min
3. ScrapingJob.mark_as_timeout()
4. Verifica can_retry() (retry_count < max_retries)
5. ScrapingJob.increment_retry()
6. Reenvía datos con send_data()
7. Si éxito: continúa procesamiento
8. Si fallo: marca como failed y espera próximo intento
```

### Reintento de Jobs Fallidos

```
1. Comando cron ejecuta auto_retry_jobs
2. Busca jobs con status='failed' o 'timeout'
3. Verifica can_retry()
4. ScrapingJob.increment_retry()
5. Lee archivo con read_file()
6. Reenvía con send_data()
7. Actualiza estado según resultado
```

## 📊 Monitoreo y Logs

### Logs de Aplicación

Los logs se guardan en:
- **logger.log**: Logs generales de la aplicación
- **/var/log/scraping_jobs.log**: Logs del comando cron (si se configura)

### Verificar Estado de Jobs

**Por comando:**
```bash
python manage.py check_scraping_jobs
```

**Por admin Django:**
- Acceder a `/admin/movil/scrapingjob/`
- Filtrar por estado
- Ver detalles de cada job

**Por shell de Django:**
```python
python manage.py shell

from movil.models import ScrapingJob
from django.contrib.auth.models import User

# Ver todos los jobs
ScrapingJob.objects.all()

# Jobs fallidos
ScrapingJob.objects.filter(status='failed')

# Jobs en timeout
ScrapingJob.objects.filter(status='timeout')

# Jobs que pueden reintentar
failed_jobs = ScrapingJob.objects.filter(status__in=['failed', 'timeout'])
[job for job in failed_jobs if job.can_retry()]

# Jobs de un usuario específico
user = User.objects.get(username='usuario')
ScrapingJob.objects.filter(user=user)

# Estadísticas
from django.db.models import Count
ScrapingJob.objects.values('status').annotate(count=Count('id'))
```

## ⚙️ Configuración

### Parámetros Configurables

En el modelo `ScrapingJob`:

```python
# Cambiar máximo de reintentos
job.max_retries = 5  # Default: 3
job.save()

# Cambiar tiempo de timeout
job.timeout_minutes = 45  # Default: 30
job.save()
```

### Variables de Entorno

Si se requiere, se pueden agregar al archivo `.env`:

```bash
# Tiempo de timeout en minutos
SCRAPING_TIMEOUT_MINUTES=30

# Máximo de reintentos
SCRAPING_MAX_RETRIES=3

# Intervalo de verificación automática (cron)
SCRAPING_CHECK_INTERVAL=15
```

## 🧪 Testing

### Probar Manualmente

```bash
# Verificar sin cambios
python manage.py check_scraping_jobs --dry-run

# Verificar con reintentos simulados
python manage.py check_scraping_jobs --dry-run --retry-failed

# Ejecutar comando automático
python manage.py auto_retry_jobs
```

### Simular Timeout

```python
from movil.models import ScrapingJob
from django.utils import timezone
from datetime import timedelta

# Crear job de prueba
job = ScrapingJob.objects.get(id=123)
job.started_at = timezone.now() - timedelta(minutes=45)
job.status = 'processing'
job.save()

# Verificar timeout
print(job.is_timed_out())  # True
```

### Simular Reintento

```python
# Marcar como fallido
job.mark_as_failed("Error de prueba")

# Verificar si puede reintentar
print(job.can_retry())  # True si retry_count < max_retries

# Reintentar
if job.can_retry():
    job.increment_retry()
    print(f"Reintento {job.retry_count}/{job.max_retries}")
```

## 🚀 Despliegue

### 1. Aplicar Migraciones

```bash
cd /opt/masterfilter
python manage.py makemigrations movil
python manage.py migrate
```

### 2. Configurar Cron

```bash
# Editar crontab
crontab -e

# Agregar línea para verificación cada 15 minutos
*/15 * * * * cd /opt/masterfilter && python manage.py auto_retry_jobs >> /var/log/scraping_jobs.log 2>&1
```

### 3. Crear Log File

```bash
sudo touch /var/log/scraping_jobs.log
sudo chown www-data:www-data /var/log/scraping_jobs.log
sudo chmod 644 /var/log/scraping_jobs.log
```

### 4. Reiniciar Servicios

```bash
# Si se usa Gunicorn
sudo systemctl restart gunicorn

# Si se usa uWSGI
sudo systemctl restart uwsgi

# Verificar logs
tail -f /var/log/scraping_jobs.log
```

## 📈 Mejoras Futuras

### Posibles Extensiones

1. **Notificaciones**
   - Email al usuario cuando un job falla después de max_retries
   - Webhook a sistema de monitoreo (Slack, Discord, etc.)

2. **Métricas Avanzadas**
   - Dashboard con estadísticas en tiempo real
   - Gráficos de éxito/fallo por usuario
   - Tiempo promedio de procesamiento

3. **Optimizaciones**
   - Sistema de cola con Celery para procesamiento asíncrono
   - Rate limiting para evitar sobrecarga de API
   - Backoff exponencial para reintentos

4. **Interfaz de Usuario**
   - Vista en frontend para ver estado de jobs
   - Botón para reintentar manualmente
   - Notificaciones en tiempo real con WebSockets

## 🆘 Troubleshooting

### Problema: Los jobs no se reintentan automáticamente

**Solución:**
1. Verificar que el cron esté configurado:
   ```bash
   crontab -l
   ```
2. Verificar logs del cron:
   ```bash
   tail -f /var/log/scraping_jobs.log
   ```
3. Ejecutar manualmente para verificar:
   ```bash
   python manage.py auto_retry_jobs
   ```

### Problema: Jobs marcados como timeout prematuramente

**Solución:**
1. Aumentar tiempo de timeout:
   ```python
   job.timeout_minutes = 60
   job.save()
   ```
2. O al ejecutar comando:
   ```bash
   python manage.py check_scraping_jobs --timeout-minutes 60
   ```

### Problema: Jobs alcanzan max_retries sin éxito

**Solución:**
1. Revisar logs para identificar error recurrente
2. Verificar conectividad con API externa
3. Aumentar max_retries si es problema temporal:
   ```python
   job.max_retries = 5
   job.retry_count = 0  # Reset contador
   job.status = 'failed'  # Para que pueda reintentar
   job.save()
   ```

## 📞 Soporte

Para más información o problemas, revisar:
- Logs de aplicación: `logger.log`
- Logs de cron: `/var/log/scraping_jobs.log`
- Admin Django: `/admin/movil/scrapingjob/`
- Documentación Django: https://docs.djangoproject.com/

---

**Fecha de implementación:** 2025-12-23  
**Versión:** 1.0  
**Autor:** Sistema de Reintentos Automáticos - Masterfilter
