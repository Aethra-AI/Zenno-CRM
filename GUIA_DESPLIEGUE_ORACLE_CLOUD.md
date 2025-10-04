# 🚀 GUÍA COMPLETA: Despliegue Backend en Oracle Cloud Infrastructure

## 📊 **RESUMEN DEL PLAN**

**VM Target:** VM.Standard.A1.Flex (2 OCPU, 12GB RAM, 2Gbps)  
**OS:** Debian Linux  
**Stack:** Python Flask + Gunicorn + Nginx + SSL  
**Objetivo:** Backend accesible desde frontend con HTTPS  

---

## 🎯 **ARQUITECTURA DEL DESPLIEGUE**

```
Internet → Oracle Cloud → Nginx (SSL/HTTPS) → Gunicorn → Flask App
                ↓
         Frontend se conecta via HTTPS
```

---

## 📋 **FASE 1: CONFIGURACIÓN DE LA VM EN ORACLE CLOUD**

### **PASO 1.1: Crear Instancia de Computación**

#### **En Oracle Cloud Console:**
1. **Navegar a:** Compute → Instances
2. **Hacer clic:** "Create Instance"

#### **Configuración Básica:**
```
Nombre: whatsapp-backend-vm
Compartimento: [Tu compartimento]
Ubicación: [Tu región]
```

#### **Configuración de Imagen:**
```
Sistema Operativo: Canonical Ubuntu 22.04 LTS (Recomendado)
Arquitectura: Arm64 (para A1.Flex)
```

#### **Configuración de Forma:**
```
Series de formas: Virtual Machine
Forma: VM.Standard.A1.Flex
OCPU: 2
Memoria (GB): 12
Ancho de banda de red (Gbps): 2
```

#### **Configuración de Red:**
```
Red virtual en la nube: [Crear nueva o usar existente]
Subred: [Crear nueva o usar existente]
Asignar una dirección IP pública: ✅ SÍ
```

#### **Configuración de Clave SSH:**
```
Clave SSH: [Subir tu clave pública o generar nueva]
```

#### **Configuración de Iniciar:**
```
Mostrar opciones avanzadas: ✅ SÍ
Origen del volumen de arranque: Imagen
Tamaño (GB): 50
```

### **PASO 1.2: Configurar Security List (Firewall)**

#### **En VCN → Security Lists:**
```
Regla de entrada:
- Puerto 22 (SSH): 0.0.0.0/0
- Puerto 80 (HTTP): 0.0.0.0/0  
- Puerto 443 (HTTPS): 0.0.0.0/0
- Puerto 5000 (Flask Dev): 0.0.0.0/0 (solo para testing)
```

---

## 📋 **FASE 2: CONFIGURACIÓN INICIAL DE LA VM**

### **PASO 2.1: Conectar a la VM**

```bash
# Obtener IP pública de la VM desde Oracle Console
ssh -i tu_clave_privada.pem ubuntu@TU_IP_PUBLICA

# Ejemplo:
# ssh -i ~/.ssh/oracle_key.pem ubuntu@129.146.123.45
```

### **PASO 2.2: Actualizar Sistema**

```bash
# Actualizar paquetes
sudo apt update && sudo apt upgrade -y

# Instalar dependencias básicas
sudo apt install -y curl wget git vim htop unzip software-properties-common
```

### **PASO 2.3: Instalar Python y Dependencias**

```bash
# Instalar Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Instalar dependencias del sistema
sudo apt install -y build-essential libssl-dev libffi-dev libmysqlclient-dev pkg-config

# Verificar instalación
python3.11 --version
pip3 --version
```

---

## 📋 **FASE 3: CONFIGURACIÓN DEL BACKEND**

### **PASO 3.1: Clonar y Preparar Proyecto**

```bash
# Crear directorio para la aplicación
sudo mkdir -p /opt/whatsapp-backend
sudo chown ubuntu:ubuntu /opt/whatsapp-backend
cd /opt/whatsapp-backend

# Clonar tu repositorio (reemplazar con tu URL)
git clone https://github.com/tu-usuario/tu-repositorio.git .

# O subir archivos manualmente
# scp -r ./bACKEND/* ubuntu@TU_IP:/opt/whatsapp-backend/
```

### **PASO 3.2: Configurar Entorno Virtual**

```bash
# Crear entorno virtual
python3.11 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Si no tienes requirements.txt, instalar manualmente:
pip install flask gunicorn mysql-connector-python python-dotenv requests
```

### **PASO 3.3: Configurar Variables de Entorno**

```bash
# Crear archivo .env
nano .env
```

**Contenido del archivo .env:**
```env
# Base de datos
DB_HOST=localhost
DB_PORT=3306
DB_USER=whatsapp_user
DB_PASSWORD=tu_password_seguro
DB_NAME=whatsapp_multi_tenant

# Flask
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=tu_clave_secreta_muy_larga_y_segura

# JWT
JWT_SECRET_KEY=tu_jwt_secret_key_muy_segura

# WhatsApp
WHATSAPP_WEBHOOK_URL=https://tu-dominio.com/api/whatsapp/webhook

# Servidor
HOST=0.0.0.0
PORT=5000
```

### **PASO 3.4: Configurar Base de Datos**

```bash
# Instalar MySQL
sudo apt install -y mysql-server

# Configurar MySQL
sudo mysql_secure_installation

# Conectar a MySQL
sudo mysql -u root -p
```

**Scripts SQL para crear base de datos:**
```sql
-- Crear usuario y base de datos
CREATE DATABASE whatsapp_multi_tenant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'whatsapp_user'@'localhost' IDENTIFIED BY 'tu_password_seguro';
GRANT ALL PRIVILEGES ON whatsapp_multi_tenant.* TO 'whatsapp_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```bash
# Ejecutar scripts de inicialización de base de datos
mysql -u whatsapp_user -p whatsapp_multi_tenant < database_setup.sql
```

---

## 📋 **FASE 4: CONFIGURACIÓN DE GUNICORN**

### **PASO 4.1: Crear Archivo de Configuración de Gunicorn**

```bash
# Crear archivo de configuración
nano /opt/whatsapp-backend/gunicorn.conf.py
```

**Contenido de gunicorn.conf.py:**
```python
# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/var/log/whatsapp-backend/access.log"
errorlog = "/var/log/whatsapp-backend/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'whatsapp-backend'

# Server mechanics
daemon = False
pidfile = '/var/run/whatsapp-backend.pid'
user = 'ubuntu'
group = 'ubuntu'
tmp_upload_dir = None

# SSL (si tienes certificados)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'
```

### **PASO 4.2: Crear Directorio de Logs**

```bash
# Crear directorio de logs
sudo mkdir -p /var/log/whatsapp-backend
sudo chown ubuntu:ubuntu /var/log/whatsapp-backend
```

### **PASO 4.3: Probar Gunicorn**

```bash
# Activar entorno virtual
source venv/bin/activate

# Probar Gunicorn
gunicorn --config gunicorn.conf.py app:app

# Verificar que funciona
curl http://localhost:5000/api/health
```

---

## 📋 **FASE 5: CONFIGURACIÓN DE SYSTEMD**

### **PASO 5.1: Crear Servicio Systemd**

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/whatsapp-backend.service
```

**Contenido del servicio:**
```ini
[Unit]
Description=WhatsApp Backend Gunicorn Application
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/whatsapp-backend
Environment="PATH=/opt/whatsapp-backend/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/opt/whatsapp-backend/venv/bin/gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### **PASO 5.2: Habilitar y Iniciar Servicio**

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicio
sudo systemctl enable whatsapp-backend.service

# Iniciar servicio
sudo systemctl start whatsapp-backend.service

# Verificar estado
sudo systemctl status whatsapp-backend.service

# Ver logs
sudo journalctl -u whatsapp-backend.service -f
```

---

## 📋 **FASE 6: CONFIGURACIÓN DE NGINX**

### **PASO 6.1: Instalar Nginx**

```bash
# Instalar Nginx
sudo apt install -y nginx

# Iniciar Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Verificar estado
sudo systemctl status nginx
```

### **PASO 6.2: Configurar Nginx como Proxy Inverso**

```bash
# Crear configuración del sitio
sudo nano /etc/nginx/sites-available/whatsapp-backend
```

**Contenido de la configuración:**
```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;  # Cambiar por tu dominio
    
    # Logs
    access_log /var/log/nginx/whatsapp-backend.access.log;
    error_log /var/log/nginx/whatsapp-backend.error.log;
    
    # Tamaño máximo de archivo
    client_max_body_size 100M;
    
    # Proxy a Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # Static files (si tienes)
    location /static/ {
        alias /opt/whatsapp-backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:5000/api/health;
        access_log off;
    }
}
```

### **PASO 6.3: Habilitar Sitio y Reiniciar Nginx**

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/whatsapp-backend /etc/nginx/sites-enabled/

# Eliminar sitio por defecto
sudo rm /etc/nginx/sites-enabled/default

# Probar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx

# Verificar estado
sudo systemctl status nginx
```

---

## 📋 **FASE 7: CONFIGURACIÓN DE SSL CON LET'S ENCRYPT**

### **PASO 7.1: Instalar Certbot**

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx
```

### **PASO 7.2: Obtener Certificado SSL**

```bash
# Obtener certificado (reemplazar con tu dominio)
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Probar renovación automática
sudo certbot renew --dry-run
```

### **PASO 7.3: Configurar Renovación Automática**

```bash
# Verificar que el cron job se creó
sudo crontab -l

# Debería mostrar algo como:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 📋 **FASE 8: CONFIGURACIÓN DE DOMINIO Y DNS**

### **PASO 8.1: Configurar DNS**

**En tu proveedor de DNS (ej: Cloudflare, Namecheap, etc.):**
```
Tipo: A
Nombre: @
Valor: TU_IP_PUBLICA_DE_ORACLE

Tipo: A  
Nombre: www
Valor: TU_IP_PUBLICA_DE_ORACLE
```

### **PASO 8.2: Verificar DNS**

```bash
# Verificar resolución DNS
nslookup tu-dominio.com
dig tu-dominio.com
```

---

## 📋 **FASE 9: CONFIGURACIÓN DE SEGURIDAD**

### **PASO 9.1: Configurar Firewall UFW**

```bash
# Instalar UFW
sudo apt install -y ufw

# Configurar reglas
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Permitir SSH
sudo ufw allow ssh

# Permitir HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Habilitar firewall
sudo ufw enable

# Verificar estado
sudo ufw status
```

### **PASO 9.2: Configurar Fail2Ban**

```bash
# Instalar Fail2Ban
sudo apt install -y fail2ban

# Crear configuración
sudo nano /etc/fail2ban/jail.local
```

**Contenido de jail.local:**
```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
```

```bash
# Reiniciar Fail2Ban
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban

# Verificar estado
sudo systemctl status fail2ban
```

---

## 📋 **FASE 10: MONITOREO Y MANTENIMIENTO**

### **PASO 10.1: Script de Monitoreo**

```bash
# Crear script de monitoreo
nano /opt/whatsapp-backend/monitor.sh
```

**Contenido del script:**
```bash
#!/bin/bash

# Script de monitoreo para WhatsApp Backend
LOG_FILE="/var/log/whatsapp-backend/monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Iniciando monitoreo..." >> $LOG_FILE

# Verificar servicio Gunicorn
if ! systemctl is-active --quiet whatsapp-backend.service; then
    echo "[$DATE] ERROR: Servicio whatsapp-backend no está activo" >> $LOG_FILE
    systemctl restart whatsapp-backend.service
    echo "[$DATE] Servicio reiniciado" >> $LOG_FILE
fi

# Verificar Nginx
if ! systemctl is-active --quiet nginx; then
    echo "[$DATE] ERROR: Nginx no está activo" >> $LOG_FILE
    systemctl restart nginx
    echo "[$DATE] Nginx reiniciado" >> $LOG_FILE
fi

# Verificar respuesta HTTP
if ! curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "[$DATE] ERROR: Backend no responde" >> $LOG_FILE
    systemctl restart whatsapp-backend.service
    echo "[$DATE] Backend reiniciado" >> $LOG_FILE
fi

echo "[$DATE] Monitoreo completado" >> $LOG_FILE
```

```bash
# Hacer ejecutable
chmod +x /opt/whatsapp-backend/monitor.sh

# Agregar al cron (cada 5 minutos)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/whatsapp-backend/monitor.sh") | crontab -
```

### **PASO 10.2: Script de Backup**

```bash
# Crear script de backup
nano /opt/whatsapp-backend/backup.sh
```

**Contenido del script:**
```bash
#!/bin/bash

# Script de backup para WhatsApp Backend
BACKUP_DIR="/opt/backups"
DATE=$(date '+%Y%m%d_%H%M%S')

# Crear directorio de backup
mkdir -p $BACKUP_DIR

# Backup de base de datos
mysqldump -u whatsapp_user -p whatsapp_multi_tenant > $BACKUP_DIR/db_backup_$DATE.sql

# Backup de archivos de aplicación
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz /opt/whatsapp-backend/

# Backup de configuraciones
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz /etc/nginx/ /etc/systemd/system/whatsapp-backend.service

# Limpiar backups antiguos (más de 7 días)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completado: $DATE"
```

```bash
# Hacer ejecutable
chmod +x /opt/whatsapp-backend/backup.sh

# Agregar al cron (diario a las 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/whatsapp-backend/backup.sh") | crontab -
```

---

## 📋 **FASE 11: CONFIGURACIÓN DEL FRONTEND**

### **PASO 11.1: Actualizar URLs en Frontend**

**En tu frontend, actualizar:**
```typescript
// config/environment.ts
export const ENV = {
  API_BASE_URL: 'https://tu-dominio.com',
  // ... resto de configuración
};
```

### **PASO 11.2: Configurar CORS en Backend**

**En app.py, verificar configuración CORS:**
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['https://tu-frontend.com', 'http://localhost:5173'])
```

---

## 📋 **FASE 12: PRUEBAS Y VERIFICACIÓN**

### **PASO 12.1: Pruebas de Conectividad**

```bash
# Probar HTTP local
curl http://localhost:5000/api/health

# Probar HTTP público
curl http://tu-dominio.com/api/health

# Probar HTTPS
curl https://tu-dominio.com/api/health

# Probar endpoint de WhatsApp
curl -H "Authorization: Bearer TU_TOKEN" https://tu-dominio.com/api/whatsapp/mode
```

### **PASO 12.2: Verificar Logs**

```bash
# Logs de la aplicación
sudo journalctl -u whatsapp-backend.service -f

# Logs de Nginx
sudo tail -f /var/log/nginx/whatsapp-backend.access.log
sudo tail -f /var/log/nginx/whatsapp-backend.error.log

# Logs de Gunicorn
tail -f /var/log/whatsapp-backend/access.log
tail -f /var/log/whatsapp-backend/error.log
```

### **PASO 12.3: Pruebas de Rendimiento**

```bash
# Instalar Apache Bench
sudo apt install -y apache2-utils

# Prueba de carga
ab -n 1000 -c 10 https://tu-dominio.com/api/health
```

---

## 🚨 **SOLUCIÓN DE PROBLEMAS COMUNES**

### **Problema: Servicio no inicia**
```bash
# Ver logs detallados
sudo journalctl -u whatsapp-backend.service -n 50

# Verificar configuración
sudo systemctl cat whatsapp-backend.service

# Probar manualmente
cd /opt/whatsapp-backend
source venv/bin/activate
gunicorn --config gunicorn.conf.py app:app
```

### **Problema: Nginx 502 Bad Gateway**
```bash
# Verificar que Gunicorn esté corriendo
ps aux | grep gunicorn

# Verificar puerto
netstat -tlnp | grep 5000

# Verificar logs de Nginx
sudo tail -f /var/log/nginx/error.log
```

### **Problema: Base de datos no conecta**
```bash
# Verificar MySQL
sudo systemctl status mysql

# Probar conexión
mysql -u whatsapp_user -p whatsapp_multi_tenant

# Verificar variables de entorno
cat /opt/whatsapp-backend/.env
```

### **Problema: SSL no funciona**
```bash
# Verificar certificado
sudo certbot certificates

# Renovar certificado
sudo certbot renew

# Verificar configuración de Nginx
sudo nginx -t
```

---

## 📊 **COMANDOS ÚTILES DE MANTENIMIENTO**

### **Comandos de Servicio:**
```bash
# Reiniciar servicios
sudo systemctl restart whatsapp-backend.service
sudo systemctl restart nginx

# Ver estado de servicios
sudo systemctl status whatsapp-backend.service
sudo systemctl status nginx

# Ver logs en tiempo real
sudo journalctl -u whatsapp-backend.service -f
```

### **Comandos de Monitoreo:**
```bash
# Ver uso de recursos
htop
df -h
free -h

# Ver conexiones de red
netstat -tlnp
ss -tlnp

# Ver logs de acceso
tail -f /var/log/nginx/whatsapp-backend.access.log
```

### **Comandos de Backup:**
```bash
# Backup manual
/opt/whatsapp-backend/backup.sh

# Restaurar base de datos
mysql -u whatsapp_user -p whatsapp_multi_tenant < backup.sql

# Restaurar aplicación
tar -xzf app_backup.tar.gz -C /
```

---

## 🎯 **CHECKLIST DE DESPLIEGUE**

### **✅ Configuración de VM:**
- [ ] VM creada en Oracle Cloud
- [ ] Security List configurado
- [ ] SSH funcionando
- [ ] Sistema actualizado

### **✅ Backend:**
- [ ] Python 3.11 instalado
- [ ] Entorno virtual creado
- [ ] Dependencias instaladas
- [ ] Variables de entorno configuradas
- [ ] Base de datos configurada

### **✅ Gunicorn:**
- [ ] Configuración creada
- [ ] Servicio systemd configurado
- [ ] Servicio iniciado y habilitado
- [ ] Logs funcionando

### **✅ Nginx:**
- [ ] Nginx instalado
- [ ] Configuración de proxy creada
- [ ] Sitio habilitado
- [ ] Nginx reiniciado

### **✅ SSL:**
- [ ] Certbot instalado
- [ ] Certificado SSL obtenido
- [ ] Renovación automática configurada

### **✅ Dominio:**
- [ ] DNS configurado
- [ ] Dominio apunta a la VM
- [ ] HTTPS funcionando

### **✅ Seguridad:**
- [ ] Firewall configurado
- [ ] Fail2Ban instalado
- [ ] Puertos cerrados innecesarios

### **✅ Monitoreo:**
- [ ] Script de monitoreo creado
- [ ] Cron jobs configurados
- [ ] Logs funcionando

---

## 🚀 **RESULTADO FINAL**

### **URLs de Acceso:**
```
Backend API: https://tu-dominio.com/api/
Health Check: https://tu-dominio.com/api/health
WhatsApp Mode: https://tu-dominio.com/api/whatsapp/mode
```

### **Servicios Activos:**
- ✅ **WhatsApp Backend** (Gunicorn + Flask)
- ✅ **Nginx** (Proxy Inverso + SSL)
- ✅ **MySQL** (Base de datos)
- ✅ **Systemd** (Gestión de servicios)
- ✅ **Let's Encrypt** (Certificados SSL)
- ✅ **Fail2Ban** (Seguridad)
- ✅ **UFW** (Firewall)

### **Monitoreo:**
- ✅ **Logs centralizados**
- ✅ **Backup automático**
- ✅ **Monitoreo de servicios**
- ✅ **Renovación SSL automática**

---

## 📞 **SOPORTE Y MANTENIMIENTO**

### **Logs Importantes:**
```bash
# Logs de aplicación
sudo journalctl -u whatsapp-backend.service

# Logs de Nginx
sudo tail -f /var/log/nginx/whatsapp-backend.access.log

# Logs de sistema
sudo tail -f /var/log/syslog
```

### **Comandos de Emergencia:**
```bash
# Reiniciar todo
sudo systemctl restart whatsapp-backend.service nginx mysql

# Ver estado completo
sudo systemctl status whatsapp-backend.service nginx mysql

# Verificar conectividad
curl -I https://tu-dominio.com/api/health
```

**¡Tu backend estará desplegado y funcionando en Oracle Cloud!** 🚀
