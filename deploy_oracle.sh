#!/bin/bash

# 🚀 Script de Despliegue Automático para Oracle Cloud
# WhatsApp Multi-Tenant Backend

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Variables de configuración
APP_DIR="/opt/whatsapp-backend"
APP_USER="ubuntu"
APP_NAME="whatsapp-backend"
DOMAIN=""
EMAIL=""

# Función para mostrar ayuda
show_help() {
    echo "🚀 Script de Despliegue Automático - WhatsApp Backend"
    echo ""
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  -d, --domain DOMAIN    Dominio para SSL (ej: mi-dominio.com)"
    echo "  -e, --email EMAIL      Email para Let's Encrypt"
    echo "  -h, --help             Mostrar esta ayuda"
    echo ""
    echo "Ejemplo:"
    echo "  $0 -d mi-dominio.com -e admin@mi-dominio.com"
    echo ""
}

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Verificar que se proporcionaron los argumentos necesarios
if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
    print_error "Faltan argumentos requeridos"
    show_help
    exit 1
fi

print_status "Iniciando despliegue de WhatsApp Backend..."
print_status "Dominio: $DOMAIN"
print_status "Email: $EMAIL"

# Verificar que estamos ejecutando como root o con sudo
if [[ $EUID -ne 0 ]]; then
    print_error "Este script debe ejecutarse como root o con sudo"
    exit 1
fi

# 1. Actualizar sistema
print_status "Actualizando sistema..."
apt update && apt upgrade -y

# 2. Instalar dependencias básicas
print_status "Instalando dependencias básicas..."
apt install -y curl wget git vim htop unzip software-properties-common \
    build-essential libssl-dev libffi-dev libmysqlclient-dev pkg-config

# 3. Instalar Python 3.11
print_status "Instalando Python 3.11..."
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# 4. Instalar MySQL
print_status "Instalando MySQL..."
apt install -y mysql-server

# 5. Instalar Nginx
print_status "Instalando Nginx..."
apt install -y nginx

# 6. Instalar Certbot
print_status "Instalando Certbot..."
apt install -y certbot python3-certbot-nginx

# 7. Instalar UFW y Fail2Ban
print_status "Instalando herramientas de seguridad..."
apt install -y ufw fail2ban

# 8. Configurar MySQL
print_status "Configurando MySQL..."
systemctl start mysql
systemctl enable mysql

# Crear base de datos y usuario
mysql -e "CREATE DATABASE IF NOT EXISTS whatsapp_multi_tenant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS 'whatsapp_user'@'localhost' IDENTIFIED BY 'WhatsApp2024!SecurePass';"
mysql -e "GRANT ALL PRIVILEGES ON whatsapp_multi_tenant.* TO 'whatsapp_user'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

print_success "MySQL configurado correctamente"

# 9. Crear directorio de aplicación
print_status "Creando directorio de aplicación..."
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

# 10. Crear directorio de logs
print_status "Creando directorios de logs..."
mkdir -p /var/log/$APP_NAME
chown $APP_USER:$APP_USER /var/log/$APP_NAME

# 11. Crear archivo de configuración de producción
print_status "Creando archivo de configuración..."
cat > $APP_DIR/.env << EOF
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
WHATSAPP_WEBHOOK_URL=https://$DOMAIN/api/whatsapp/webhook
WHATSAPP_BRIDGE_URL=http://localhost:3000

# Servidor
HOST=127.0.0.1
PORT=5000
WORKERS=4
TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/$APP_NAME/app.log
EOF

chown $APP_USER:$APP_USER $APP_DIR/.env

# 12. Crear archivo de configuración de Gunicorn
print_status "Creando configuración de Gunicorn..."
cat > $APP_DIR/gunicorn.conf.py << 'EOF'
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
EOF

chown $APP_USER:$APP_USER $APP_DIR/gunicorn.conf.py

# 13. Crear servicio systemd
print_status "Creando servicio systemd..."
cat > /etc/systemd/system/$APP_NAME.service << 'EOF'
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
EOF

# 14. Crear configuración de Nginx
print_status "Creando configuración de Nginx..."
cat > /etc/nginx/sites-available/$APP_NAME << EOF
# Upstream para Gunicorn
upstream whatsapp_backend {
    server 127.0.0.1:5000;
    keepalive 32;
}

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Logging
    access_log /var/log/nginx/$APP_NAME.access.log;
    error_log /var/log/nginx/$APP_NAME.error.log;
    
    # Client settings
    client_max_body_size 100M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # Main location - API endpoints
    location /api/ {
        proxy_pass http://whatsapp_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
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
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts normales para webhooks
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
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
EOF

# 15. Configurar Nginx
print_status "Configurando Nginx..."
ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

# 16. Configurar firewall
print_status "Configurando firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

# 17. Configurar Fail2Ban
print_status "Configurando Fail2Ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
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
EOF

systemctl restart fail2ban
systemctl enable fail2ban

# 18. Crear script de monitoreo
print_status "Creando script de monitoreo..."
cat > $APP_DIR/monitor.sh << 'EOF'
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
EOF

chmod +x $APP_DIR/monitor.sh
chown $APP_USER:$APP_USER $APP_DIR/monitor.sh

# 19. Crear script de backup
print_status "Creando script de backup..."
mkdir -p /opt/backups
chown $APP_USER:$APP_USER /opt/backups

cat > $APP_DIR/backup.sh << 'EOF'
#!/bin/bash

# Script de backup para WhatsApp Backend
BACKUP_DIR="/opt/backups"
DATE=$(date '+%Y%m%d_%H%M%S')

# Crear directorio de backup
mkdir -p $BACKUP_DIR

# Backup de base de datos
mysqldump -u whatsapp_user -pWhatsApp2024!SecurePass whatsapp_multi_tenant > $BACKUP_DIR/db_backup_$DATE.sql

# Backup de archivos de aplicación
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz /opt/whatsapp-backend/

# Backup de configuraciones
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz /etc/nginx/ /etc/systemd/system/whatsapp-backend.service

# Limpiar backups antiguos (más de 7 días)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completado: $DATE"
EOF

chmod +x $APP_DIR/backup.sh
chown $APP_USER:$APP_USER $APP_DIR/backup.sh

# 20. Configurar cron jobs
print_status "Configurando cron jobs..."
(crontab -u $APP_USER -l 2>/dev/null; echo "*/5 * * * * $APP_DIR/monitor.sh") | crontab -u $APP_USER -
(crontab -u $APP_USER -l 2>/dev/null; echo "0 2 * * * $APP_DIR/backup.sh") | crontab -u $APP_USER -

# 21. Iniciar servicios
print_status "Iniciando servicios..."
systemctl daemon-reload
systemctl enable $APP_NAME.service
systemctl start nginx

print_success "Configuración del servidor completada!"

# 22. Instrucciones finales
print_status "🎯 PASOS SIGUIENTES:"
echo ""
print_warning "1. Sube tu código de aplicación a $APP_DIR"
print_warning "2. Crea el entorno virtual y instala dependencias:"
echo "   cd $APP_DIR"
echo "   python3.11 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
print_warning "3. Inicializa la base de datos:"
echo "   python init_database_final.py"
echo ""
print_warning "4. Inicia el servicio:"
echo "   sudo systemctl start $APP_NAME.service"
echo ""
print_warning "5. Obtén certificado SSL:"
echo "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo ""
print_warning "6. Verifica que todo funciona:"
echo "   curl https://$DOMAIN/health"
echo "   curl https://$DOMAIN/api/health"
echo ""

print_success "¡Despliegue del servidor completado!"
print_status "Tu backend estará disponible en: https://$DOMAIN"
print_status "API Health Check: https://$DOMAIN/api/health"
