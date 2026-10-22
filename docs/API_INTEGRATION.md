# Guía de Integración - Sentinel Worker + Oracle API

Esta guía explica cómo conectar el Sentinel Worker (AWS EC2) con la Oracle API (On-Premise).

---

## 🏗️ Arquitectura

```
┌─────────────────────┐         ┌──────────────────────┐
│   Sentinel Worker   │         │     Oracle API       │
│     (AWS EC2)       │ ◄─────► │   (On-Premise/VPN)   │
│                     │  HTTPS  │                      │
│  - ApiClient        │         │  - FastAPI           │
│  - BatchProcessor   │         │  - OracleDB Client   │
│  - ImageProcessor   │         │                      │
└─────────────────────┘         └──────────────────────┘
         │                                 │
         │                                 │
         ▼                                 ▼
┌─────────────────────┐         ┌──────────────────────┐
│  PostgreSQL (RDS)   │         │   Oracle Database    │
│  - Lightsail DB     │         │   (Corporate Net)    │
└─────────────────────┘         └──────────────────────┘
```

---

## 📋 Configuración del Sentinel Worker

### 1. Variables de Entorno Requeridas

El worker necesita estas variables para conectarse a la API:

```bash
# Oracle API Configuration
ORACLE_API_URL=https://api.tudominio.com  # URL pública de la API
ORACLE_API_KEY=tu-clave-secreta-aqui      # La misma que configuraste en la API

# PostgreSQL Configuration (sin cambios)
POSTGRES_DB_HOST=ls-16385948f6f603e3495d0f8cf941752490b88cf7.ceb0k2co66dq.us-east-1.rds.amazonaws.com
POSTGRES_DB_NAME=test_sentinel
POSTGRES_DB_USER=dbmasteruser
POSTGRES_DB_PASS=tu-password-postgres
```

### 2. Actualizar el Comando Docker

**Antes (con conexión directa a Oracle):**
```bash
docker run -d \
  -e ORACLE_DB_USER="..." \
  -e ORACLE_DB_PASS="..." \
  -e ORACLE_DB_DSN="..." \
  sentinel-worker
```

**Ahora (con API):**
```bash
docker run -d --restart always \
  -v /home/ec2-user/app/models:/app/models \
  -e ORACLE_API_URL="https://api.tudominio.com" \
  -e ORACLE_API_KEY="clave-secreta-123" \
  -e POSTGRES_DB_HOST="ls-16385948f6f603e3495d0f8cf941752490b88cf7.ceb0k2co66dq.us-east-1.rds.amazonaws.com" \
  -e POSTGRES_DB_NAME="test_sentinel" \
  -e POSTGRES_DB_USER="dbmasteruser" \
  -e POSTGRES_DB_PASS="tu-password" \
  sentinel-worker --days-back 1
```

---

## 🔧 Configuración de la Oracle API

### 1. Desplegar la API On-Premise

Sigue la guía `DEPLOYMENT.md` en el proyecto `sentinel-oracle-api`.

**Opción recomendada: Docker**
```bash
cd /ruta/a/sentinel-oracle-api

docker build -t oracle-api .
docker run -d --restart unless-stopped \
  -p 8000:8000 \
  -e ORACLE_DB_USER="MT002692" \
  -e ORACLE_DB_PASS="OIRJCN38" \
  -e ORACLE_DB_DSN="10.240.66.165:1521/ISGLGUA" \
  -e ORACLE_API_KEY="clave-secreta-123" \
  oracle-api
```

### 2. Exponer la API (Opcional pero Recomendado)

**Opción A: Nginx Reverse Proxy con HTTPS**

```nginx
server {
    listen 443 ssl;
    server_name api.tudominio.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-API-KEY $http_x_api_key;
    }
}
```

**Opción B: Túnel Cloudflare (si no tienes IP pública)**

```bash
# Instalar cloudflared
# Linux
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared

# Crear túnel
cloudflared tunnel --url http://localhost:8000
```

---

## 🧪 Pruebas de Integración

### 1. Probar la API Localmente

```bash
# Health check
curl http://localhost:8000/health

# Endpoint con datos (requiere API key)
curl -H "X-API-KEY: clave-secreta-123" \
  "http://localhost:8000/images/pending?date=2026-02-08&page=1&page_size=10"
```

### 2. Probar desde Sentinel (Mock)

```bash
cd c:/SENTINEL2-FUNCIONAL-19-DIC-2024-MODEL-3
python tests/test_api_integration.py
```

Deberías ver:
```
✅ ApiClient initialization test passed
✅ Single page fetch test passed
✅ Multiple page fetch test passed (1500 records)
✅ API authentication header test passed
✅ Date formatting test passed
✅ Error handling test passed
```

### 3. Prueba End-to-End (Real)

**En el servidor de la API:**
```bash
# Ver logs en tiempo real
docker logs -f oracle-api
```

**En AWS EC2:**
```bash
# Ejecutar Sentinel manualmente para 1 día
docker run --rm \
  -v /home/ec2-user/app/models:/app/models \
  -e ORACLE_API_URL="https://api.tudominio.com" \
  -e ORACLE_API_KEY="clave-secreta-123" \
  -e POSTGRES_DB_HOST="..." \
  -e POSTGRES_DB_NAME="test_sentinel" \
  -e POSTGRES_DB_USER="dbmasteruser" \
  -e POSTGRES_DB_PASS="password" \
  sentinel-worker --days-back 1
```

**Logs esperados:**
```
INFO - Oracle API client initialized at https://api.tudominio.com
INFO - Fetching images from API for date: 2026-02-07
INFO - Total images fetched from API: 35247
INFO - Processing date: 2026-02-07
Processed 100/35247 images
Processed 200/35247 images
...
```

---

## 🔒 Seguridad

### 1. Generar API Key Segura

```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

### 2. Rotar la API Key

1. Generar nueva key
2. Actualizar en la API: `docker restart oracle-api` con nueva env var
3. Actualizar en Sentinel: `docker restart sentinel-worker` con nueva env var

### 3. Restricciones de Red (Opcional)

**En el servidor de la API (iptables):**
```bash
# Permitir solo desde la IP de AWS EC2
sudo iptables -A INPUT -p tcp --dport 8000 -s 18.232.147.18 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j DROP
```

---

## 📊 Monitoreo

### Métricas Clave

1. **Latencia de API**: Tiempo de respuesta por página
2. **Throughput**: Registros procesados por segundo
3. **Errores**: Rate de fallos en requests

### Logs

**API:**
```bash
docker logs oracle-api | grep "Fetching images"
```

**Sentinel:**
```bash
docker logs sentinel-worker | grep "Total images fetched"
```

---

## 🔧 Troubleshooting

### Error: "Connection refused"
- ✅ Verificar que la API está corriendo: `curl http://localhost:8000/health`
- ✅ Verificar firewall/puertos abiertos
- ✅ Verificar URL correcta en `ORACLE_API_URL`

### Error: "403 Forbidden"
- ✅ Verificar que `ORACLE_API_KEY` coincide en ambos lados
- ✅ Verificar que el header `X-API-KEY` se está enviando

### Error: "Timeout"
- ✅ Aumentar timeout en `core/api_client.py` (línea con `timeout=30`)
- ✅ Verificar conectividad de red entre AWS y On-Premise

### Rendimiento Lento
- ✅ Aumentar `page_size` en la API (default 1000, max 5000)
- ✅ Optimizar query de Oracle (índices en `F_ACTUAL`, `TIP_FOTO`)
- ✅ Considerar cache en la API para requests repetidos
