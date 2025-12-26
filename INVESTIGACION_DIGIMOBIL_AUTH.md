# INVESTIGACIÓN: PROBLEMA DE AUTENTICACIÓN DIGIMOBIL

**Fecha:** 2025-12-15
**Estado:** 🔴 API ROTA - Login anónimo ya no funciona

---

## 🎯 RESUMEN EJECUTIVO

La API de DigiMobil que el sistema usaba para identificar operadores telefónicos **ha cambiado su mecanismo de autenticación** y ya no permite acceso anónimo. Esto ha dejado el sistema **completamente inoperativo** para procesar números nuevos.

### Evidencia del problema:

```bash
POST https://store-backend.digimobil.es/v1/users/login
Body: {}
Headers: {}

Response: 401 Unauthorized
{
  "_error": {
    "message": "Credentials not found",
    "code": "store-backend-es-release-app-sw-048-401"
  }
}
```

---

## 📊 HALLAZGOS DE LA INVESTIGACIÓN

### 1. **Análisis del Token JWT Anterior**

El sistema anteriormente obtenía tokens JWT con esta estructura:

```json
{
  "sub": null,
  "iss": "https:///index.php",
  "cid": "https://store-api.digimobil.es",
  "iat": 1729763849,
  "exp": 1729764449,  // ⏱️ Expira en 10 minutos
  "scope": "read write",
  "data": {
    "id": null,
    "anon": true,      // ✅ Sesión anónima
    "ip": "185.47.131.53",
    "session_uid": "1729763849397088",
    "us": 100,
    "c": 1
  }
}
```

**Características:**
- `anon: true` → Indica sesión anónima
- Expiración: 10 minutos desde emisión
- No requería credenciales previas
- Se obtenía con POST vacío a `/v1/users/login`

**Fecha del último token funcional:** 2024-10-24 05:07:29
(Hardcodeado en `/opt/apimovil/app/browser.py:269`)

### 2. **Código Actual de Autenticación**

**Ubicación:** `/opt/apimovil/app/browser.py:176-181`

```python
def login(self):
    url = "https://store-backend.digimobil.es/v1/users/login"
    payload = {}      # ❌ POST vacío
    headers = {}      # ❌ Sin headers
    response = requests.request("POST", url, headers=headers,
                               data=payload,
                               proxies=self.proxies[self.position]["proxy"])
    return json.loads(response.text)
```

**Problema:** Este método ya no funciona. Retorna 401 siempre.

### 3. **Intentos de Solución Probados**

Se probaron las siguientes variaciones **SIN ÉXITO:**

| Intento | Método | Resultado |
|---------|--------|-----------|
| POST vacío | `{}` sin headers | 401 |
| POST con Content-Type | `{"Content-Type": "application/json"}` | 401 |
| Headers de navegador | User-Agent completo | 401 |
| Headers + Origin | Con Referer y Origin | 401 (con CORS habilitado) |
| Con cookies de sesión | Después de GET a la web | 401 |

### 4. **Endpoints Alternativos Verificados**

| Endpoint | Status | Nota |
|----------|--------|------|
| `/v2/users/login` | 404 | No existe |
| `/v1/auth/login` | 404 | No existe |
| `/v1/users/anonymous` | 404 | No existe |
| `/oauth/token` | 404 | No usa OAuth2 |
| `/v2/operators` | 401 | Existe pero requiere JWT |
| `/v2/operators/by-line-code/{phone}` | 401 | Requiere JWT válido |

### 5. **Configuración de Proxies**

El sistema tiene **2 proxies LunaProxy configurados:**

```
ID: 5429
  IP: eu.5j81o23u.lunaproxy.net:12233
  Username: user-gino001_B9wcY-region-es-sessid-esg5fmvkpiy2r7...
  Password: Gino001
  User: gino13122025

ID: 5430
  IP: eu.5j81o23u.lunaproxy.net:12233
  Username: user-gino001_B9wcY-region-es-sessid-esjiyzc9i2qw23...
  Password: Gino001
  User: ginorobertocruzcosme@gmail.com
```

**Nota:** Los proxies funcionan correctamente, el problema es la autenticación con DigiMobil.

---

## 🔍 TEORÍAS SOBRE EL CAMBIO

### Teoría A: Sistema de API Keys
DigiMobil agregó un sistema de API keys que requiere:
- Registrarse en un portal de desarrolladores
- Obtener `client_id` y `client_secret`
- Enviar credenciales en header o body

**Probabilidad:** 🟡 Media

### Teoría B: Requiere sesión web previa
La API ahora requiere:
- Visitar la web primero
- Obtener un cookie/token de sesión
- Usar ese token en las peticiones API

**Probabilidad:** 🟢 Alta

### Teoría C: Cambio a OAuth2/OpenID
Implementaron OAuth2 estándar:
- Authorization endpoint
- Token endpoint
- Client credentials flow

**Probabilidad:** 🔴 Baja (no hay endpoints OAuth)

### Teoría D: Bloqueo intencional
DigiMobil detectó el scraping y bloqueó el acceso:
- Solo accesible desde su web oficial
- Protección anti-bot mejorada
- Requiere interacción humana

**Probabilidad:** 🟡 Media-Alta

---

## 💡 SOLUCIONES PROPUESTAS

### Solución 1: 🤖 Usar Selenium/Playwright (RECOMENDADA)

**Descripción:**
Simular un navegador real para obtener el token desde la página web.

**Ventajas:**
- ✅ Ya tienen Selenium instalado (`views.py:462-526`)
- ✅ Pueden reutilizar código existente
- ✅ Funcionará mientras la web funcione
- ✅ No requiere credenciales especiales

**Desventajas:**
- ❌ Más lento (carga navegador)
- ❌ Mayor consumo de recursos
- ❌ Dependiente de cambios en la web

**Implementación:**

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import json

def get_digimobil_token_with_selenium():
    """Obtener token de DigiMobil usando Selenium"""

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Remote(
        command_executor='http://127.0.0.1:4444/wd/hub',
        options=chrome_options
    )

    try:
        # 1. Cargar la página
        driver.get("https://tienda.digimobil.es/")

        # 2. Interceptar peticiones de red para capturar el token
        # Opción A: Usar Chrome DevTools Protocol
        # Opción B: Buscar en localStorage/sessionStorage
        # Opción C: Buscar en cookies

        # Ejemplo con localStorage:
        token = driver.execute_script("return localStorage.getItem('auth_token')")

        # O buscar en cookies:
        cookies = driver.get_cookies()
        for cookie in cookies:
            if 'token' in cookie['name'].lower():
                token = cookie['value']
                break

        return token

    finally:
        driver.quit()
```

**Esfuerzo:** 2-3 días
**Riesgo:** Bajo

---

### Solución 2: 🔎 Ingeniería Inversa del JavaScript

**Descripción:**
Analizar los archivos JavaScript de la web para encontrar cómo generan el token.

**Pasos:**
1. Descargar archivos .js de `tienda.digimobil.es`
2. Buscar función de login/autenticación
3. Replicar la lógica en Python
4. Usar la misma lógica para generar tokens

**Ventajas:**
- ✅ Solución más rápida si se encuentra
- ✅ No requiere navegador
- ✅ Menor consumo de recursos

**Desventajas:**
- ❌ JavaScript puede estar ofuscado
- ❌ Puede cambiar frecuentemente
- ❌ Requiere skills de reversing

**Esfuerzo:** 1-2 semanas
**Riesgo:** Alto

---

### Solución 3: 🌐 Usar API Alternativa

**Descripción:**
Cambiar a un servicio de terceros para identificar operadores.

**Opciones:**

#### A) Twilio Lookup API
```python
from twilio.rest import Client

client = Client(account_sid, auth_token)
number = client.lookups.v1.phone_numbers('+34612345678').fetch()
print(number.carrier['name'])  # Nombre del operador
```

**Costo:** ~$0.005 por lookup
**Confiabilidad:** ⭐⭐⭐⭐⭐

#### B) NumVerify API
```python
import requests

response = requests.get(
    'http://apilayer.net/api/validate',
    params={
        'access_key': 'YOUR_KEY',
        'number': '34612345678'
    }
)
data = response.json()
print(data['carrier'])  # Operador
```

**Costo:** Plan gratuito: 250/mes, Pagado: desde $9.99/mes
**Confiabilidad:** ⭐⭐⭐⭐

#### C) CNMC (Base de datos oficial)
```
https://numeracionyoperadores.cnmc.es/
```

**Costo:** Gratuito
**Problema:** No tiene API pública, requiere scraping

**Ventajas:**
- ✅ Solución estable a largo plazo
- ✅ Soporte oficial
- ✅ Actualizado constantemente

**Desventajas:**
- ❌ Costo recurrente
- ❌ Requiere cuenta/suscripción
- ❌ Cambio de arquitectura

**Esfuerzo:** 3-5 días
**Riesgo:** Bajo

---

### Solución 4: 📞 Contactar DigiMobil Oficialmente

**Descripción:**
Solicitar acceso oficial a su API.

**Pasos:**
1. Contactar soporte técnico de DigiMobil
2. Explicar el uso caso
3. Solicitar API key o credenciales
4. Firmar acuerdo de uso (si requieren)

**Ventajas:**
- ✅ Solución legal y oficial
- ✅ Soporte garantizado
- ✅ Estabilidad a largo plazo

**Desventajas:**
- ❌ Pueden rechazar la solicitud
- ❌ Posible costo
- ❌ Proceso lento (semanas/meses)
- ❌ Pueden no tener API pública

**Esfuerzo:** 1-2 meses (gestión)
**Riesgo:** Alto (pueden rechazar)

---

## 🎯 RECOMENDACIÓN FINAL

**Solución Inmediata (Esta semana):**
👉 **Opción 1: Selenium** para interceptar token de la web

**Solución a Mediano Plazo (1-2 meses):**
👉 **Opción 3: Migrar a Twilio Lookup** para tener API estable

**Acciones Paralelas:**
1. Intentar contactar DigiMobil (Solución 4)
2. Documentar todo el proceso
3. Monitorear cambios en la web de DigiMobil

---

## 📝 PRÓXIMOS PASOS

### Inmediatos:
1. ✅ Investigación completada
2. ⏳ Decidir solución a implementar
3. ⏳ Asignar recursos/tiempo

### Si eligen Solución 1 (Selenium):
1. Revisar código de Selenium existente (views.py:462-526)
2. Modificar para capturar token en lugar de procesar formulario
3. Integrar en la clase DigiPhone
4. Probar con números reales
5. Monitorear estabilidad

### Si eligen Solución 3 (API Alternativa):
1. Crear cuentas en Twilio/NumVerify
2. Obtener API keys
3. Crear nueva clase para el servicio elegido
4. Migrar código de DigiPhone
5. Actualizar tests
6. Deploy gradual (mantener DigiMobil como fallback)

---

## 📊 MÉTRICAS DEL PROBLEMA

```
Sistema actual:
├─ Estado: 🔴 ROTO
├─ Números procesados últimos 7 días: 0
├─ Última consulta exitosa: ~2024-10-24
├─ Procesos pausados: 1
├─ Procesos en cola: 0
└─ Impacto: 100% del sistema inoperativo
```

---

## 🔗 REFERENCIAS

- Código de autenticación: `/opt/apimovil/app/browser.py:176-228`
- Logs de error: `/opt/apimovil/logger.log`
- Configuración de proxies: Base de datos → Tabla `app_proxy`
- Documentación de monitoreo: `/opt/masterfilter/GUIA_MONITOREO_API.md`

---

**Última actualización:** 2025-12-15 02:30 UTC
**Investigado por:** Sistema de análisis automático
