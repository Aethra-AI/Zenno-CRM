# 🚀 INSTRUCCIONES FINALES: Despliegue en Oracle Cloud

## 📋 **RESUMEN DEL PROCESO**

Has creado una **VM.Standard.A1.Flex** en Oracle Cloud con:
- ✅ **2 OCPU, 12GB RAM, 2Gbps**
- ✅ **Ubuntu 22.04 LTS**
- ✅ **IP pública asignada**

---

## 🎯 **PASOS A SEGUIR AHORA**

### **PASO 1: Conectar a tu VM**

```bash
# Usa la IP pública que Oracle te asignó
ssh -i tu_clave_privada.pem ubuntu@TU_IP_PUBLICA

# Ejemplo:
# ssh -i ~/.ssh/oracle_key.pem ubuntu@129.146.123.45
```

### **PASO 2: Ejecutar Script de Despliegue**

```bash
# Descargar el script de despliegue
wget https://raw.githubusercontent.com/tu-repo/deploy_oracle.sh
# O subirlo manualmente vía SCP

# Hacer ejecutable
chmod +x deploy_oracle.sh

# Ejecutar el script (reemplaza con tu dominio y email)
sudo ./deploy_oracle.sh -d tu-dominio.com -e tu-email@ejemplo.com

# Ejemplo:
# sudo ./deploy_oracle.sh -d whatsapp-backend.mi-dominio.com -e admin@mi-dominio.com
```

### **PASO 3: Subir tu Código**

```bash
# Opción A: Usar Git (recomendado)
cd /opt/whatsapp-backend
git clone https://github.com/tu-usuario/tu-repositorio.git .

# Opción B: Subir archivos manualmente desde tu máquina local
# scp -i tu_clave_privada.pem -r ./bACKEND/* ubuntu@TU_IP:/opt/whatsapp-backend/
```

### **PASO 4: Configurar Entorno Python**

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

# O si tienes requirements.txt:
# pip install -r requirements.txt
```

### **PASO 5: Inicializar Base de Datos**

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar script de inicialización
python init_database_final.py

# Verificar que se crearon las tablas
mysql -u whatsapp_user -p whatsapp_multi_tenant -e "SHOW TABLES;"
```

### **PASO 6: Iniciar el Servicio**

```bash
# Iniciar el servicio
sudo systemctl start whatsapp-backend.service

# Habilitar para que inicie automáticamente
sudo systemctl enable whatsapp-backend.service

# Verificar estado
sudo systemctl status whatsapp-backend.service
```

### **PASO 7: Configurar SSL**

```bash
# Obtener certificado SSL
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Verificar certificado
sudo certbot certificates
```

### **PASO 8: Verificar que Todo Funciona**

```bash
# Verificar servicios
sudo systemctl status whatsapp-backend.service nginx mysql

# Probar endpoints
curl http://localhost:5000/api/health
curl https://tu-dominio.com/health
curl https://tu-dominio.com/api/health
```

---

## 🔧 **CONFIGURACIÓN DE DOMINIO**

### **Si tienes un dominio:**

1. **Configurar DNS** en tu proveedor (Cloudflare, Namecheap, etc.):
   ```
   Tipo: A
   Nombre: @
   Valor: TU_IP_PUBLICA_DE_ORACLE
   
   Tipo: A
   Nombre: www
   Valor: TU_IP_PUBLICA_DE_ORACLE
   ```

2. **Esperar propagación DNS** (5-30 minutos)

3. **Obtener certificado SSL**:
   ```bash
   sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
   ```

### **Si NO tienes un dominio:**

Puedes usar la IP pública directamente:
- **Backend:** `http://TU_IP_PUBLICA/api/`
- **Health Check:** `http://TU_IP_PUBLICA/health`

---

## 📊 **VERIFICACIÓN FINAL**

### **Comandos de Verificación:**

```bash
# 1. Verificar servicios activos
sudo systemctl is-active whatsapp-backend.service nginx mysql

# 2. Verificar puertos abiertos
sudo netstat -tlnp | grep -E ':(80|443|5000|3306)'

# 3. Verificar logs
sudo journalctl -u whatsapp-backend.service -n 20

# 4. Probar API
curl https://tu-dominio.com/api/health

# 5. Verificar base de datos
mysql -u whatsapp_user -p whatsapp_multi_tenant -e "SELECT 1;"
```

### **URLs de Acceso:**

```
✅ Health Check: https://tu-dominio.com/health
✅ API Backend: https://tu-dominio.com/api/
✅ WhatsApp Mode: https://tu-dominio.com/api/whatsapp/mode
✅ Login: https://tu-dominio.com/api/auth/login
```

---

## 🚨 **SOLUCIÓN DE PROBLEMAS**

### **Problema: Servicio no inicia**
```bash
# Ver logs detallados
sudo journalctl -u whatsapp-backend.service -n 50

# Probar manualmente
cd /opt/whatsapp-backend
source venv/bin/activate
python app.py
```

### **Problema: Error 502 Bad Gateway**
```bash
# Verificar que Gunicorn esté corriendo
ps aux | grep gunicorn

# Verificar puerto
sudo netstat -tlnp | grep 5000

# Reiniciar servicios
sudo systemctl restart whatsapp-backend.service nginx
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

---

## 📱 **CONFIGURACIÓN DEL FRONTEND**

### **Actualizar URLs en tu frontend:**

```typescript
// config/environment.ts
export const ENV = {
  API_BASE_URL: 'https://tu-dominio.com',
  // ... resto de configuración
};
```

### **Configurar CORS en backend:**

```python
# En app.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=[
    'https://tu-frontend.com',
    'http://localhost:5173',  # Para desarrollo
    'https://tu-dominio-frontend.com'
])
```

---

## 🔐 **CONFIGURACIÓN DE SEGURIDAD**

### **Firewall configurado automáticamente:**
- ✅ **Puerto 22** (SSH) - Permitido
- ✅ **Puerto 80** (HTTP) - Permitido  
- ✅ **Puerto 443** (HTTPS) - Permitido
- ❌ **Puerto 5000** (Flask) - Solo local

### **Fail2Ban activo:**
- ✅ **Protección SSH**
- ✅ **Protección Nginx**
- ✅ **Rate limiting**

---

## 📊 **MONITOREO Y MANTENIMIENTO**

### **Scripts automáticos creados:**
- ✅ **Monitoreo cada 5 minutos**
- ✅ **Backup diario a las 2 AM**
- ✅ **Logs centralizados**

### **Comandos útiles:**
```bash
# Ver logs en tiempo real
sudo journalctl -u whatsapp-backend.service -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/whatsapp-backend.access.log

# Backup manual
/opt/whatsapp-backend/backup.sh

# Monitoreo manual
/opt/whatsapp-backend/monitor.sh
```

---

## 🎯 **CHECKLIST FINAL**

### **✅ Verificaciones obligatorias:**
- [ ] **VM creada** en Oracle Cloud
- [ ] **SSH funcionando** a la VM
- [ ] **Script de despliegue** ejecutado
- [ ] **Código subido** a /opt/whatsapp-backend
- [ ] **Entorno virtual** creado y dependencias instaladas
- [ ] **Base de datos** inicializada
- [ ] **Servicio** whatsapp-backend iniciado
- [ ] **Nginx** configurado y funcionando
- [ ] **SSL** configurado (si tienes dominio)
- [ ] **API respondiendo** correctamente
- [ ] **Frontend** configurado con nueva URL

---

## 🚀 **RESULTADO FINAL**

### **Tu backend estará disponible en:**
```
🌐 https://tu-dominio.com/api/
🏥 https://tu-dominio.com/health
📱 https://tu-dominio.com/api/whatsapp/mode
🔐 https://tu-dominio.com/api/auth/login
```

### **Servicios activos:**
- ✅ **WhatsApp Backend** (Gunicorn + Flask)
- ✅ **Nginx** (Proxy Inverso + SSL)
- ✅ **MySQL** (Base de datos)
- ✅ **Systemd** (Gestión de servicios)
- ✅ **Let's Encrypt** (Certificados SSL)
- ✅ **Fail2Ban** (Seguridad)
- ✅ **UFW** (Firewall)

---

## 📞 **SOPORTE**

### **Si necesitas ayuda:**
1. **Verificar logs:** `sudo journalctl -u whatsapp-backend.service -f`
2. **Verificar servicios:** `sudo systemctl status whatsapp-backend.service nginx mysql`
3. **Verificar conectividad:** `curl https://tu-dominio.com/api/health`

### **Archivos importantes:**
- **Configuración:** `/opt/whatsapp-backend/.env`
- **Logs:** `/var/log/whatsapp-backend/`
- **Backups:** `/opt/backups/`
- **Servicio:** `/etc/systemd/system/whatsapp-backend.service`

**¡Tu backend WhatsApp estará desplegado y funcionando en Oracle Cloud!** 🎉
