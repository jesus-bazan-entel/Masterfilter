# GUÍA DE MONITOREO - API DigiMobil

## 📋 ÍNDICE

1. [Ubicación de Logs](#ubicación-de-logs)
2. [Ver Consultas a DigiMobil](#ver-consultas-a-digimobil)
3. [Monitorear Números Procesados](#monitorear-números-procesados)
4. [Ver Logs en Tiempo Real](#ver-logs-en-tiempo-real)
5. [Consultar Base de Datos](#consultar-base-de-datos)
6. [Troubleshooting](#troubleshooting)

---

## 📁 UBICACIÓN DE LOGS

### Logs del Backend API (apimovil)
```bash
/opt/apimovil/logger.log              # Log principal (6 MB)
/opt/apimovil/daphne.log              # Servidor HTTP (5 MB)
/opt/apimovil/django_debug.log        # Debug detallado (2.7 GB) ⚠️
/opt/apimovil/logs/celery_worker.log  # Worker asíncrono
```

### Logs del Frontend (masterfilter)
```bash
/opt/masterfilter/logger.log          # Log principal (163 MB) ⚠️
```

---

## 🔍 VER CONSULTAS A DIGIMOBIL

### Opción 1: Buscar en logs por número específico

```bash
# Buscar todas las consultas de un número
grep "612345678" /opt/apimovil/logger.log

# Ver solo el resultado final (operador detectado)
grep "612345678" /opt/apimovil/logger.log | grep "Phone:"
```

**Ejemplo de salida:**
```
INFO:root:[+] Phone: 612345678 - Operator: VODAFONE ESPANA, S.A.U. - IP: Pending - Usuario: username - File: archivo.xlsx - Thread: 2
```

### Opción 2: Ver últimas consultas procesadas

```bash
# Últimas 50 consultas exitosas
tail -100 /opt/apimovil/logger.log | grep "Phone:" | tail -50

# Con formato más legible
tail -100 /opt/apimovil/logger.log | grep "Phone:" | awk -F' - ' '{print $1 "\n  Operador: " $2 "\n  IP: " $3 "\n  Archivo: " $5 "\n"}'
```

### Opción 3: Ver el request/response completo

```bash
# Ver requests HTTP a DigiMobil (cuando está logueado)
grep "response.text" /opt/apimovil/logger.log | tail -20
```

**Formato del log:**
```python
# El código loguea así (browser.py:166):
logging.info(f"response.text: {response.text}")
```

---

## 📊 MONITOREAR NÚMEROS PROCESADOS

### Script de Monitoreo

He creado un script Python que consulta la base de datos directamente:

```bash
# Ver estadísticas generales
/opt/apimovil/venv/bin/python /opt/apimovil/monitor_api.py --stats

# Ver procesos activos
/opt/apimovil/venv/bin/python /opt/apimovil/monitor_api.py --processes

# Buscar historial de un número específico
/opt/apimovil/venv/bin/python /opt/apimovil/monitor_api.py --phone 612345678

# Ver todo (procesos + últimos números + estadísticas)
/opt/apimovil/venv/bin/python /opt/apimovil/monitor_api.py
```

**Ejemplo de salida:**
```
====================================================================================================
PROCESOS EN EJECUCIÓN
====================================================================================================

🟢 ACTIVO       | archivo_20241215.xlsx
   Progreso:   234/ 5000 ( 4.7%)
   Usuario:  username
   Creado:   2025-12-15 10:30:00

====================================================================================================
ÚLTIMOS 20 NÚMEROS PROCESADOS
====================================================================================================

✅ 2025-12-15 10:45:23 | 612345678    | VODAFONE ESPANA, S.A.U.                  | Pending         | archivo.xlsx
✅ 2025-12-15 10:45:22 | 687654321    | ORANGE ESPAGNE S.A.U.                   | Pending         | archivo.xlsx
```

---

## 🔴 VER LOGS EN TIEMPO REAL

### Opción 1: Monitor con colores

```bash
# Ejecutar el script de monitoreo en tiempo real
/opt/apimovil/tail_logs.sh
```

Este script muestra:
- **Verde**: Números procesados exitosamente
- **Rojo**: Errores y excepciones
- **Blanco**: Otros logs

### Opción 2: Comando manual

```bash
# Ver todos los logs en tiempo real
tail -f /opt/apimovil/logger.log

# Solo números procesados
tail -f /opt/apimovil/logger.log | grep "Phone:"

# Solo errores
tail -f /opt/apimovil/logger.log | grep -E "Error|Exception"

# Múltiples archivos simultáneamente
tail -f /opt/apimovil/logger.log /opt/apimovil/daphne.log
```

---

## 💾 CONSULTAR BASE DE DATOS

### Opción 1: Django Shell

```bash
cd /opt/apimovil
/opt/apimovil/venv/bin/python manage.py shell
```

```python
from app.models import Movil, Consecutive

# Ver últimos 10 números procesados
for m in Movil.objects.all().order_by('-fecha_hora')[:10]:
    print(f"{m.number} → {m.operator} (IP: {m.ip})")

# Buscar un número específico
Movil.objects.filter(number="612345678")

# Ver historial completo de un número
for m in Movil.objects.filter(number="612345678").order_by('-fecha_hora'):
    print(f"{m.fecha_hora}: {m.operator} - {m.file}")

# Ver procesos activos
Consecutive.objects.filter(active=True)

# Estadísticas por operador
from django.db.models import Count
Movil.objects.values('operator').annotate(count=Count('operator')).order_by('-count')
```

### Opción 2: SQL Directo

```bash
# Conectar a PostgreSQL
docker exec -it postgres_container psql -U admin -d db_masterfilter
```

```sql
-- Ver últimos números procesados
SELECT number, operator, ip, fecha_hora, file
FROM app_movil
ORDER BY fecha_hora DESC
LIMIT 20;

-- Buscar número específico
SELECT * FROM app_movil WHERE number = '612345678';

-- Contar por operador
SELECT operator, COUNT(*) as total
FROM app_movil
GROUP BY operator
ORDER BY total DESC;

-- Ver procesos activos
SELECT * FROM app_consecutive WHERE active = true;
```

---

## 🔧 TROUBLESHOOTING

### Problema 1: No veo logs de consultas

**Verificar que el servicio esté corriendo:**
```bash
ps aux | grep "daphne.*8800"
netstat -tlnp | grep 8800
```

**Verificar últimos logs:**
```bash
tail -50 /opt/apimovil/logger.log
tail -50 /opt/apimovil/daphne.log
```

### Problema 2: La API DigiMobil retorna 401

**Verificación:**
```bash
# Ver errores 401 en los logs
grep "401" /opt/apimovil/logger.log | tail -20
```

**Causa:** La API de DigiMobil cambió y ahora requiere credenciales.

**Solución:** Verificar el código de autenticación en `/opt/apimovil/app/browser.py`

### Problema 3: Los números se quedan en "Pending"

**Verificar:**
```bash
# Ver si hay errores de proxy
grep "Error1 83\|Error2 94" /opt/apimovil/logger.log | tail -20

# Ver estado de proxies
cd /opt/apimovil
/opt/apimovil/venv/bin/python manage.py shell -c "
from app.models import Proxy
for p in Proxy.objects.all():
    print(f'{p.username} - {p.ip}:{p.port_min} - User: {p.user.username if p.user else None}')
"
```

### Problema 4: El proceso se detiene

**Verificar workers:**
```bash
# Ver procesos activos
/opt/apimovil/venv/bin/python /opt/apimovil/monitor_api.py --processes

# Ver en logs si el proceso finalizó
grep "Proceso finalizado\|Proceso pausado" /opt/apimovil/logger.log | tail -10
```

---

## 📝 FORMATO DE LOGS

### Log de número procesado exitosamente
```
INFO:root:[+] Phone: 612345678 - Operator: VODAFONE ESPANA, S.A.U. - IP: Pending - Usuario: username@email.com - File: archivo.xlsx - Thread: 2
```

**Campos:**
- `Phone`: Número consultado
- `Operator`: Operador detectado
- `IP`: IP del proxy usado (o "Pending" si usa cache)
- `Usuario`: Usuario que subió el archivo
- `File`: Nombre del archivo Excel
- `Thread`: ID del worker (0-3)

### Log de error en consulta
```
INFO:root:[-] Thread:2 - IP: Pending - proxy_password - username@email.com - Error1 83: Connection timeout
```

**Campos:**
- `Thread`: ID del worker
- `IP`: IP del proxy
- `Error1 83` o `Error2 94`: Tipo de error
- Mensaje: Descripción del error

### Log de inicio de proceso
```
INFO:root:Processing task: 612345678 username@email.com archivo.xlsx
```

### Log de fin de proceso
```
INFO:root:Proceso finalizado: archivo.xlsx
```

---

## 🚀 COMANDOS RÁPIDOS

```bash
# Ver actividad en tiempo real
/opt/apimovil/tail_logs.sh

# Ver estadísticas
/opt/apimovil/venv/bin/python /opt/apimovil/monitor_api.py --stats

# Buscar número
/opt/apimovil/venv/bin/python /opt/apimovil/monitor_api.py --phone 612345678

# Ver últimos 100 números procesados
tail -200 /opt/apimovil/logger.log | grep "Phone:" | tail -100

# Ver errores recientes
tail -200 /opt/apimovil/logger.log | grep -E "Error|Exception" | tail -50

# Ver requests HTTP al servidor
tail -100 /opt/apimovil/daphne.log | grep "POST /process/"
```

---

## ⚠️ IMPORTANTE

1. **Logs grandes**: Los archivos de log son muy grandes. Considera implementar rotación:
   ```bash
   # django_debug.log: 2.7 GB ⚠️
   # logger.log: 163 MB (masterfilter) + 6 MB (apimovil)
   ```

2. **Cache de 30 días**: Los números consultados hace menos de 30 días se toman de cache (BD) sin consultar DigiMobil.

3. **Estado actual**: La API de DigiMobil requiere ahora credenciales (error 401 en login anónimo).

---

**Última actualización:** 2025-12-15
**Autor:** Sistema MasterFilter
