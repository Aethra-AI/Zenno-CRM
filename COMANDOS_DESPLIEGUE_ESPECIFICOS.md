# 🔧 COMANDOS ESPECÍFICOS PARA TU BACKEND WHATSAPP

## 📋 **COMANDOS DE PREPARACIÓN**

### **1. Crear requirements.txt**
```bash
# En tu máquina local, crear requirements.txt
cd bACKEND
pip freeze > requirements.txt
```

### **2. Preparar archivos para subir**
```bash
# Crear archivo de configuración específico para producción
nano production.env
```

**Contenido de production.env:**
```env
# Base de datos MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=whatsapp_user
DB_PASSWORD=WhatsApp2024!SecurePass
DB_NAME=whatsapp_multi_tenant

# Flask
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=WhatsApp-Backend-2024-Super-Secret-Key-For-Production-Use-Only

# JWT
JWT_SECRET_KEY=JWT-Secret-Key-WhatsApp-2024-Production-Environment-Secure

# WhatsApp
WHATSAPP_WEBHOOK_URL=https://tu-dominio.com/api/whatsapp/webhook
WHATSAPP_BRIDGE_URL=http://localhost:3000

# Servidor
HOST=127.0.0.1
PORT=5000
WORKERS=4
TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/whatsapp-backend/app.log
```

---

## 📋 **COMANDOS DE SUBIDA A LA VM**

### **Opción 1: Subir archivos vía SCP**
```bash
# Desde tu máquina local
scp -i tu_clave_privada.pem -r ./bACKEND/* ubuntu@TU_IP:/opt/whatsapp-backend/

# Ejemplo:
# scp -i ~/.ssh/oracle_key.pem -r ./bACKEND/* ubuntu@129.146.123.45:/opt/whatsapp-backend/
```

### **Opción 2: Usar Git (Recomendado)**
```bash
# En la VM, clonar tu repositorio
cd /opt/whatsapp-backend
git clone https://github.com/tu-usuario/tu-repositorio.git .

# O si ya tienes archivos subidos, hacer pull
git pull origin main
```

---

## 📋 **COMANDOS DE CONFIGURACIÓN EN LA VM**

### **1. Configurar entorno virtual específico**
```bash
cd /opt/whatsapp-backend

# Crear entorno virtual con Python 3.11
python3.11 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias específicas para tu backend
pip install --upgrade pip
pip install flask==2.3.3
pip install gunicorn==21.2.0
pip install mysql-connector-python==8.1.0
pip install python-dotenv==1.0.0
pip install requests==2.31.0
pip install bcrypt==4.0.1
pip install PyJWT==2.8.0
pip install flask-cors==4.0.0
pip install cryptography==41.0.4
```

### **2. Configurar base de datos específica**
```bash
# Conectar a MySQL
sudo mysql -u root -p

# Ejecutar estos comandos SQL:
```

```sql
-- Crear base de datos específica para WhatsApp
CREATE DATABASE whatsapp_multi_tenant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario específico
CREATE USER 'whatsapp_user'@'localhost' IDENTIFIED BY 'WhatsApp2024!SecurePass';

-- Dar permisos
GRANT ALL PRIVILEGES ON whatsapp_multi_tenant.* TO 'whatsapp_user'@'localhost';
FLUSH PRIVILEGES;

-- Verificar
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User = 'whatsapp_user';
EXIT;
```

### **3. Ejecutar scripts de inicialización**
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar script de inicialización de base de datos
python init_database_final.py

# Verificar que se crearon las tablas
mysql -u whatsapp_user -p whatsapp_multi_tenant -e "SHOW TABLES;"
```

---

## 📋 **CONFIGURACIÓN ESPECÍFICA DE GUNICORN**

### **Crear gunicorn.conf.py específico para tu backend**
```bash
nano /opt/whatsapp-backend/gunicorn.conf.py
```

**Contenido específico:**
```python
# Gunicorn configuration para WhatsApp Backend
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes - optimizado para VM A1.Flex (2 OCPU)
workers = 4  # 2 OCPU * 2 = 4 workers
worker_class = "sync"
worker_connections = 1000
timeout = 60  # Aumentado para WhatsApp
keepalive = 5

# Restart workers
max_requests = 1000
max_requests_jitter = 100

# Logging específico para WhatsApp
accesslog = "/var/log/whatsapp-backend/access.log"
errorlog = "/var/log/whatsapp-backend/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s %(p)s'

# Process naming
proc_name = 'whatsapp-backend'

# Server mechanics
daemon = False
pidfile = '/var/run/whatsapp-backend.pid'
user = 'ubuntu'
group = 'ubuntu'

# Preload app for better performance
preload_app = True

# Worker timeout for long-running requests
worker_tmp_dir = '/dev/shm'

# Environment variables
raw_env = [
    'FLASK_ENV=production',
    'PYTHONPATH=/opt/whatsapp-backend',
]
```

---

## 📋 **CONFIGURACIÓN ESPECÍFICA DE SYSTEMD**

### **Crear servicio systemd optimizado**
```bash
sudo nano /etc/systemd/system/whatsapp-backend.service
```

**Contenido optimizado:**
```ini
[Unit]
Description=WhatsApp Multi-Tenant Backend
After=network.target mysql.service
Requires=mysql.service
StartLimitInterval=0

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/whatsapp-backend
Environment="PATH=/opt/whatsapp-backend/venv/bin"
Environment="FLASK_ENV=production"
Environment="PYTHONPATH=/opt/whatsapp-backend"

# Comando específico para tu app
ExecStart=/opt/whatsapp-backend/venv/bin/gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID

# Restart policy
Restart=always
RestartSec=10
StartLimitBurst=3

# Process management
KillMode=mixed
TimeoutStopSec=30
PrivateTmp=true

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/whatsapp-backend /var/log/whatsapp-backend

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=whatsapp-backend

[Install]
WantedBy=multi-user.target
```

---

## 📋 **CONFIGURACIÓN ESPECÍFICA DE NGINX**

### **Configuración optimizada para WhatsApp**
```bash
sudo nano /etc/nginx/sites-available/whatsapp-backend
```

**Contenido optimizado:**
```nginx
# Upstream para Gunicorn
upstream whatsapp_backend {
    server 127.0.0.1:5000;
    keepalive 32;
}

server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;
    
    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logging
    access_log /var/log/nginx/whatsapp-backend.access.log;
    error_log /var/log/nginx/whatsapp-backend.error.log;
    
    # Client settings
    client_max_body_size 100M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # Main location - API endpoints
    location /api/ {
        proxy_pass http://whatsapp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts específicos para WhatsApp
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;  # 5 minutos para webhooks
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
        
        # Keep-alive
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://whatsapp_backend/api/health;
        access_log off;
    }
    
    # WhatsApp webhook endpoint (sin timeout largo)
    location /api/whatsapp/webhook {
        proxy_pass http://whatsapp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts normales para webhooks
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Static files (si tienes)
    location /static/ {
        alias /opt/whatsapp-backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ \.(env|log|conf)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

---

## 📋 **COMANDOS DE INICIALIZACIÓN**

### **1. Crear directorios necesarios**
```bash
# Crear directorios de logs
sudo mkdir -p /var/log/whatsapp-backend
sudo chown ubuntu:ubuntu /var/log/whatsapp-backend

# Crear directorio de backups
sudo mkdir -p /opt/backups
sudo chown ubuntu:ubuntu /opt/backups
```

### **2. Configurar permisos**
```bash
# Dar permisos correctos
sudo chown -R ubuntu:ubuntu /opt/whatsapp-backend
sudo chmod +x /opt/whatsapp-backend/*.py
```

### **3. Probar la aplicación manualmente**
```bash
cd /opt/whatsapp-backend
source venv/bin/activate

# Probar que la app funciona
python -c "import app; print('App imports OK')"

# Probar Gunicorn
gunicorn --config gunicorn.conf.py app:app &

# Probar endpoint
curl http://localhost:5000/api/health

# Matar proceso de prueba
pkill -f gunicorn
```

---

## 📋 **COMANDOS DE DESPLIEGUE FINAL**

### **1. Habilitar y iniciar servicios**
```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicios
sudo systemctl enable whatsapp-backend.service
sudo systemctl enable nginx
sudo systemctl enable mysql

# Iniciar servicios
sudo systemctl start whatsapp-backend.service
sudo systemctl start nginx

# Verificar estado
sudo systemctl status whatsapp-backend.service
sudo systemctl status nginx
```

### **2. Configurar SSL**
```bash
# Obtener certificado SSL
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Verificar certificado
sudo certbot certificates
```

### **3. Configurar firewall**
```bash
# Configurar UFW
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Verificar
sudo ufw status
```

---

## 📋 **COMANDOS DE VERIFICACIÓN**

### **1. Verificar que todo funciona**
```bash
# Verificar servicios
sudo systemctl status whatsapp-backend.service nginx mysql

# Verificar puertos
sudo netstat -tlnp | grep -E ':(80|443|5000|3306)'

# Verificar logs
sudo journalctl -u whatsapp-backend.service -n 20
sudo tail -n 20 /var/log/nginx/whatsapp-backend.access.log
```

### **2. Probar endpoints**
```bash
# Probar health check
curl -I https://tu-dominio.com/health

# Probar API
curl -I https://tu-dominio.com/api/health

# Probar con token (después de hacer login)
curl -H "Authorization: Bearer TU_TOKEN" https://tu-dominio.com/api/whatsapp/mode
```

### **3. Verificar base de datos**
```bash
# Conectar a base de datos
mysql -u whatsapp_user -p whatsapp_multi_tenant

# Verificar tablas
SHOW TABLES;

# Verificar usuarios
SELECT * FROM users LIMIT 5;
```

---

## 📋 **COMANDOS DE MANTENIMIENTO**

### **1. Actualizar aplicación**
```bash
cd /opt/whatsapp-backend

# Hacer backup
./backup.sh

# Actualizar código
git pull origin main

# Reiniciar servicio
sudo systemctl restart whatsapp-backend.service

# Verificar
sudo systemctl status whatsapp-backend.service
```

### **2. Ver logs en tiempo real**
```bash
# Logs de aplicación
sudo journalctl -u whatsapp-backend.service -f

# Logs de Nginx
sudo tail -f /var/log/nginx/whatsapp-backend.access.log

# Logs de error
sudo tail -f /var/log/nginx/whatsapp-backend.error.log
```

### **3. Monitorear recursos**
```bash
# Uso de CPU y memoria
htop

# Espacio en disco
df -h

# Conexiones de red
ss -tlnp | grep -E ':(80|443|5000|3306)'
```

---

## 🚨 **COMANDOS DE EMERGENCIA**

### **1. Si el servicio no inicia**
```bash
# Ver logs detallados
sudo journalctl -u whatsapp-backend.service -n 100

# Probar manualmente
cd /opt/whatsapp-backend
source venv/bin/activate
python app.py

# Si hay errores, revisar:
cat .env
mysql -u whatsapp_user -p whatsapp_multi_tenant -e "SHOW TABLES;"
```

### **2. Si Nginx da error 502**
```bash
# Verificar que Gunicorn esté corriendo
ps aux | grep gunicorn

# Verificar puerto
sudo netstat -tlnp | grep 5000

# Reiniciar todo
sudo systemctl restart whatsapp-backend.service nginx
```

### **3. Si hay problemas de SSL**
```bash
# Verificar certificado
sudo certbot certificates

# Renovar certificado
sudo certbot renew --force-renewal

# Verificar configuración Nginx
sudo nginx -t
```

---

## 🎯 **CHECKLIST FINAL**

### **✅ Verificaciones obligatorias:**
```bash
# 1. Servicios activos
sudo systemctl is-active whatsapp-backend.service nginx mysql

# 2. Puertos abiertos
sudo netstat -tlnp | grep -E ':(80|443|5000|3306)'

# 3. SSL funcionando
curl -I https://tu-dominio.com/health

# 4. API respondiendo
curl https://tu-dominio.com/api/health

# 5. Base de datos conectada
mysql -u whatsapp_user -p whatsapp_multi_tenant -e "SELECT 1;"

# 6. Logs sin errores críticos
sudo journalctl -u whatsapp-backend.service --since "1 hour ago" | grep -i error
```

**¡Con estos comandos tendrás tu backend WhatsApp desplegado y funcionando en Oracle Cloud!** 🚀
