# 📋 COMANDOS COPY-PASTE PARA ORACLE CLOUD

## 🚀 **COMANDOS PARA EJECUTAR EN LA VM**

### **1. Conectar a la VM**
```bash
ssh -i tu_clave_privada.pem ubuntu@TU_IP_PUBLICA
```

### **2. Descargar y ejecutar script de despliegue**
```bash
# Descargar el script (ajustar URL según tu repositorio)
wget https://raw.githubusercontent.com/tu-usuario/tu-repo/main/bACKEND/deploy_oracle.sh

# Hacer ejecutable
chmod +x deploy_oracle.sh

# Ejecutar script (REEMPLAZAR con tu dominio y email)
sudo ./deploy_oracle.sh -d tu-dominio.com -e tu-email@ejemplo.com
```

### **3. Subir código de aplicación**
```bash
# Opción A: Git
cd /opt/whatsapp-backend
git clone https://github.com/tu-usuario/tu-repositorio.git .

# Opción B: Desde tu máquina local
# scp -i tu_clave_privada.pem -r ./bACKEND/* ubuntu@TU_IP:/opt/whatsapp-backend/
```

### **4. Configurar entorno Python**
```bash
cd /opt/whatsapp-backend

# Crear entorno virtual
python3.11 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
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

### **5. Inicializar base de datos**
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar script de inicialización
python init_database_final.py

# Verificar tablas creadas
mysql -u whatsapp_user -p whatsapp_multi_tenant -e "SHOW TABLES;"
```

### **6. Iniciar servicios**
```bash
# Iniciar servicio backend
sudo systemctl start whatsapp-backend.service

# Habilitar inicio automático
sudo systemctl enable whatsapp-backend.service

# Verificar estado
sudo systemctl status whatsapp-backend.service
```

### **7. Configurar SSL (si tienes dominio)**
```bash
# Obtener certificado SSL
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Verificar certificado
sudo certbot certificates
```

### **8. Verificar funcionamiento**
```bash
# Verificar servicios
sudo systemctl status whatsapp-backend.service nginx mysql

# Probar endpoints
curl http://localhost:5000/api/health
curl https://tu-dominio.com/health
curl https://tu-dominio.com/api/health
```

---

## 🔧 **COMANDOS DE VERIFICACIÓN**

### **Verificar servicios activos**
```bash
sudo systemctl is-active whatsapp-backend.service nginx mysql
```

### **Verificar puertos abiertos**
```bash
sudo netstat -tlnp | grep -E ':(80|443|5000|3306)'
```

### **Ver logs en tiempo real**
```bash
sudo journalctl -u whatsapp-backend.service -f
```

### **Ver logs de Nginx**
```bash
sudo tail -f /var/log/nginx/whatsapp-backend.access.log
```

### **Verificar base de datos**
```bash
mysql -u whatsapp_user -p whatsapp_multi_tenant -e "SELECT 1;"
```

---

## 🚨 **COMANDOS DE SOLUCIÓN DE PROBLEMAS**

### **Si el servicio no inicia**
```bash
# Ver logs detallados
sudo journalctl -u whatsapp-backend.service -n 50

# Probar manualmente
cd /opt/whatsapp-backend
source venv/bin/activate
python app.py
```

### **Si hay error 502 Bad Gateway**
```bash
# Verificar que Gunicorn esté corriendo
ps aux | grep gunicorn

# Verificar puerto 5000
sudo netstat -tlnp | grep 5000

# Reiniciar servicios
sudo systemctl restart whatsapp-backend.service nginx
```

### **Si la base de datos no conecta**
```bash
# Verificar MySQL
sudo systemctl status mysql

# Probar conexión
mysql -u whatsapp_user -p whatsapp_multi_tenant

# Verificar variables de entorno
cat /opt/whatsapp-backend/.env
```

### **Si hay problemas de SSL**
```bash
# Verificar certificado
sudo certbot certificates

# Renovar certificado
sudo certbot renew --force-renewal

# Verificar configuración Nginx
sudo nginx -t
```

---

## 📊 **COMANDOS DE MANTENIMIENTO**

### **Reiniciar servicios**
```bash
sudo systemctl restart whatsapp-backend.service
sudo systemctl restart nginx
sudo systemctl restart mysql
```

### **Ver estado de todos los servicios**
```bash
sudo systemctl status whatsapp-backend.service nginx mysql
```

### **Ver uso de recursos**
```bash
htop
df -h
free -h
```

### **Backup manual**
```bash
/opt/whatsapp-backend/backup.sh
```

### **Monitoreo manual**
```bash
/opt/whatsapp-backend/monitor.sh
```

---

## 🔐 **COMANDOS DE SEGURIDAD**

### **Verificar firewall**
```bash
sudo ufw status
```

### **Verificar Fail2Ban**
```bash
sudo systemctl status fail2ban
sudo fail2ban-client status
```

### **Ver conexiones de red**
```bash
sudo netstat -tlnp
sudo ss -tlnp
```

---

## 📱 **COMANDOS PARA CONFIGURAR FRONTEND**

### **Desde tu máquina local, actualizar frontend:**
```bash
# Editar archivo de configuración
# zenno-canvas-flow-main/src/config/environment.ts

# Cambiar:
API_BASE_URL: 'https://tu-dominio.com'

# O si no tienes dominio:
API_BASE_URL: 'http://TU_IP_PUBLICA'
```

### **Verificar CORS en backend:**
```bash
# En la VM, verificar configuración CORS en app.py
cat /opt/whatsapp-backend/app.py | grep -i cors
```

---

## 🎯 **COMANDOS DE TESTING**

### **Probar API con curl**
```bash
# Health check
curl https://tu-dominio.com/api/health

# Login (reemplazar con credenciales reales)
curl -X POST https://tu-dominio.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@crm.com", "password": "admin123"}'

# WhatsApp mode (después de login, usar token)
curl -H "Authorization: Bearer TU_TOKEN" \
  https://tu-dominio.com/api/whatsapp/mode
```

### **Probar desde navegador**
```
https://tu-dominio.com/health
https://tu-dominio.com/api/health
```

---

## 📋 **CHECKLIST DE VERIFICACIÓN**

### **Ejecutar estos comandos para verificar que todo funciona:**
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

---

## 🚀 **COMANDOS FINALES**

### **Una vez que todo esté funcionando:**
```bash
# Verificar estado completo
sudo systemctl status whatsapp-backend.service nginx mysql

# Ver logs de acceso
sudo tail -n 20 /var/log/nginx/whatsapp-backend.access.log

# Probar endpoint completo
curl -v https://tu-dominio.com/api/health
```

### **URLs finales de tu backend:**
```
✅ Health Check: https://tu-dominio.com/health
✅ API Backend: https://tu-dominio.com/api/
✅ WhatsApp Mode: https://tu-dominio.com/api/whatsapp/mode
✅ Login: https://tu-dominio.com/api/auth/login
```

**¡Tu backend WhatsApp estará desplegado y funcionando!** 🎉
