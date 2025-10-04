# 📋 DOCUMENTACIÓN COMPLETA DEL PROYECTO EN VM ORACLE CLOUD

## 🖥️ **INFORMACIÓN DEL SERVIDOR**

### **Detalles de la VM:**
- **Proveedor**: Oracle Cloud Infrastructure (OCI)
- **Ubicación**: Colombia Central (Bogotá)
- **IP Pública**: `149.130.160.182`
- **IP Privada**: `10.0.0.48`
- **Sistema Operativo**: Ubuntu 22.04.5 LTS (aarch64)
- **Arquitectura**: ARM64
- **Recursos**: VM.Standard.A1.Flex (2 OCPU, 12 GB RAM)
- **Usuario SSH**: `ubuntu`
- **Directorio de trabajo**: `/opt/whatsapp-backend`

---

## 📁 **ESTRUCTURA DE CARPETAS Y ARCHIVOS**

```
/opt/whatsapp-backend/
├── app.py                          # Aplicación Flask principal
├── requirements.txt                 # Dependencias Python
├── .env                           # Variables de entorno
├── gunicorn.conf.py               # Configuración Gunicorn
├── database_complete_setup.sql    # Script completo de base de datos
├── venv/                          # Entorno virtual Python
│   ├── bin/
│   │   ├── python3
│   │   ├── pip
│   │   └── gunicorn
│   └── lib/python3.10/site-packages/
├── logs/                          # Directorio de logs
│   ├── gunicorn_access.log
│   └── gunicorn_error.log
├── temp_uploads/                  # Archivos temporales
├── sessions/                      # Sesiones de usuario
└── migrations/                    # Migraciones de base de datos
```

### **Archivos de configuración importantes:**
- **app.py**: Aplicación Flask principal (71666 tokens)
- **requirements.txt**: Dependencias Python instaladas
- **.env**: Variables de entorno de la aplicación
- **gunicorn.conf.py**: Configuración del servidor WSGI

---

## 🗄️ **ESTRUCTURA DE BASE DE DATOS**

### **Base de datos**: `whatsapp_backend`
### **Usuario**: `whatsapp_user`
### **Host**: `localhost`

### **Tablas creadas (16 total):**

1. **Afiliado_Tags** - Relación candidatos-etiquetas
   - `id_afiliado` (INT, PK)
   - `id_tag` (INT, PK)
   - `tenant_id` (INT, PK)
   - `fecha_asignacion` (TIMESTAMP)

2. **Afiliados** - Candidatos
   - `id_afiliado` (INT, PK, AUTO_INCREMENT)
   - `fecha_registro` (TIMESTAMP)
   - `nombre_completo` (VARCHAR(255))
   - `identidad` (VARCHAR(20), UNIQUE)
   - `telefono` (VARCHAR(20))
   - `email` (VARCHAR(255))
   - `experiencia` (TEXT)
   - `ciudad` (VARCHAR(100))
   - `grado_academico` (VARCHAR(100))
   - `cv_url` (VARCHAR(500))
   - `observaciones` (TEXT)
   - `contrato_url` (VARCHAR(500))
   - `disponibilidad_rotativos` (BOOLEAN)
   - `transporte_propio` (BOOLEAN)
   - `estado` (VARCHAR(50))
   - `puntuacion` (DECIMAL(3,2))
   - `ultima_actualizacion` (TIMESTAMP)
   - `tenant_id` (INT)
   - `disponibilidad` (VARCHAR(100))
   - `linkedin` (VARCHAR(255))
   - `portfolio` (VARCHAR(255))
   - `skills` (TEXT)
   - `comentarios` (TEXT)

3. **Clientes** - Empresas
   - `id_cliente` (INT, PK, AUTO_INCREMENT)
   - `empresa` (VARCHAR(255))
   - `contacto_nombre` (VARCHAR(255))
   - `telefono` (VARCHAR(20))
   - `email` (VARCHAR(255))
   - `sector` (VARCHAR(100))
   - `observaciones` (TEXT)
   - `fecha_registro` (TIMESTAMP)
   - `tenant_id` (INT)

4. **Contratados** - Candidatos contratados
   - `id_contratacion` (INT, PK, AUTO_INCREMENT)
   - `id_afiliado` (INT, FK)
   - `id_vacante` (INT, FK)
   - `fecha_contratacion` (TIMESTAMP)
   - `salario_final` (DECIMAL(10,2))
   - `fecha_inicio` (TIMESTAMP)
   - `observaciones` (TEXT)
   - `tenant_id` (INT)

5. **Email_Templates** - Plantillas de email
   - `id_template` (INT, PK, AUTO_INCREMENT)
   - `nombre_plantilla` (VARCHAR(255))
   - `asunto` (VARCHAR(255))
   - `cuerpo_html` (TEXT)
   - `tenant_id` (INT)
   - `fecha_creacion` (TIMESTAMP)

6. **Entrevistas** - Entrevistas programadas
   - `id_entrevista` (INT, PK, AUTO_INCREMENT)
   - `id_postulacion` (INT, FK)
   - `fecha_hora` (TIMESTAMP)
   - `entrevistador` (VARCHAR(255))
   - `resultado` (VARCHAR(50))
   - `observaciones` (TEXT)
   - `tenant_id` (INT)

7. **Postulaciones** - Aplicaciones de candidatos
   - `id_postulacion` (INT, PK, AUTO_INCREMENT)
   - `id_afiliado` (INT, FK)
   - `id_vacante` (INT, FK)
   - `fecha_aplicacion` (TIMESTAMP)
   - `estado` (VARCHAR(50))
   - `comentarios` (TEXT)
   - `tenant_id` (INT)

8. **Tags** - Etiquetas para candidatos
   - `id_tag` (INT, PK, AUTO_INCREMENT)
   - `nombre_tag` (VARCHAR(100))
   - `tenant_id` (INT)
   - `fecha_creacion` (TIMESTAMP)

9. **Tenants** - Multi-tenant
   - `id` (INT, PK, AUTO_INCREMENT)
   - `nombre_empresa` (VARCHAR(100))
   - `email_contacto` (VARCHAR(100))
   - `telefono` (VARCHAR(20))
   - `direccion` (TEXT)
   - `plan` (VARCHAR(20))
   - `api_key` (VARCHAR(255), UNIQUE)
   - `activo` (BOOLEAN)
   - `fecha_creacion` (TIMESTAMP)
   - `fecha_actualizacion` (TIMESTAMP)

10. **UserSessions** - Sesiones de usuario
    - `id` (INT, PK, AUTO_INCREMENT)
    - `user_id` (INT, FK)
    - `session_token` (VARCHAR(255), UNIQUE)
    - `expires_at` (TIMESTAMP)
    - `created_at` (TIMESTAMP)

11. **Users** - Usuarios del sistema
    - `id` (INT, PK, AUTO_INCREMENT)
    - `email` (VARCHAR(255), UNIQUE)
    - `password_hash` (VARCHAR(255))
    - `name` (VARCHAR(255), NULL)
    - `tenant_id` (INT, FK)
    - `role` (VARCHAR(50))
    - `is_active` (BOOLEAN)
    - `created_at` (TIMESTAMP)
    - `updated_at` (TIMESTAMP)

12. **Vacantes** - Ofertas de trabajo
    - `id_vacante` (INT, PK, AUTO_INCREMENT)
    - `id_cliente` (INT, FK)
    - `cargo_solicitado` (VARCHAR(255))
    - `descripcion` (TEXT)
    - `requisitos` (TEXT)
    - `salario_min` (DECIMAL(10,2))
    - `salario_max` (DECIMAL(10,2))
    - `ciudad` (VARCHAR(100))
    - `estado` (VARCHAR(50))
    - `fecha_apertura` (TIMESTAMP)
    - `fecha_cierre` (TIMESTAMP)
    - `tenant_id` (INT)

13. **WhatsApp_Config** - Configuración WhatsApp
    - `id` (INT, PK, AUTO_INCREMENT)
    - `tenant_id` (INT, FK)
    - `api_type` (VARCHAR(50))
    - `config_type` (VARCHAR(50))
    - `config_data` (JSON)
    - `is_active` (BOOLEAN)
    - `created_at` (TIMESTAMP)

14. **Whatsapp_Templates** - Plantillas WhatsApp
    - `id_template` (INT, PK, AUTO_INCREMENT)
    - `nombre_plantilla` (VARCHAR(255))
    - `cuerpo_mensaje` (TEXT)
    - `tenant_id` (INT)
    - `fecha_creacion` (TIMESTAMP)

15. **puntuaciones_candidato** - Sistema de puntuación
    - `id` (INT, PK, AUTO_INCREMENT)
    - `id_afiliado` (INT, FK)
    - `puntuacion` (DECIMAL(3,2))
    - `criterios` (JSON)
    - `fecha_calculo` (TIMESTAMP)
    - `tenant_id` (INT)

16. **tenants** - Tabla legacy (mantener por compatibilidad)
    - `id` (INT, PK, AUTO_INCREMENT)
    - `name` (VARCHAR(255))
    - `created_at` (TIMESTAMP)

---

## 🐍 **DEPENDENCIAS PYTHON INSTALADAS**

### **Archivo requirements.txt:**
```
Flask==2.3.3
Flask-CORS==4.0.0
Flask-JWT-Extended==4.5.3
PyMySQL==1.1.0
python-dotenv==1.0.0
requests==2.31.0
celery==5.3.4
redis==5.0.1
bcrypt==4.1.2
python-dateutil==2.8.2
pytz==2023.3
Pillow==10.1.0
openai==1.3.7
google-generativeai==0.3.2
httpx==0.24.1
gunicorn==23.0.0
```

### **Versiones específicas instaladas:**
- **Python**: 3.10.12
- **OpenAI**: 1.3.7 (versión compatible)
- **httpx**: 0.24.1 (versión compatible con OpenAI 1.3.7)
- **Gunicorn**: 23.0.0

---

## ⚙️ **CONFIGURACIÓN DE VARIABLES DE ENTORNO**

### **Archivo .env:**
```env
DB_HOST=localhost
DB_USER=whatsapp_user
DB_PASSWORD=WhatsApp2025Secure123!
DB_NAME=whatsapp_backend
DB_PORT=3306
JWT_SECRET_KEY=your-secret-key-here
FLASK_ENV=production
WHATSAPP_WEB_PORT=3000
WHATSAPP_API_PORT=5000
OPENAI_API_KEY=sk-test-key-placeholder
GEMINI_API_KEY=test-gemini-key-placeholder
```

---

## 🗄️ **CONFIGURACIÓN DE MYSQL**

### **Credenciales:**
- **Usuario**: `whatsapp_user`
- **Contraseña**: `WhatsApp2025Secure123!`
- **Base de datos**: `whatsapp_backend`
- **Host**: `localhost`
- **Puerto**: `3306`

### **Archivo ~/.my.cnf:**
```ini
[client]
user = whatsapp_user
password = WhatsApp2025Secure123!
host = localhost
database = whatsapp_backend
```

### **Datos iniciales insertados:**
- **Tenant por defecto**: ID=1, nombre='Default Tenant'
- **Usuario admin**: email='admin@crm.com', role='admin'
- **Plantilla WhatsApp**: ID=1, mensaje por defecto

---

## 🚀 **ESTADO ACTUAL DEL DESPLIEGUE**

### **✅ COMPLETADO:**
- ✅ VM Oracle Cloud configurada
- ✅ Base de datos MySQL funcionando
- ✅ Todas las tablas creadas
- ✅ Backend Flask funcionando
- ✅ Entorno virtual configurado
- ✅ Dependencias instaladas
- ✅ Usuario admin creado
- ✅ Sistema WhatsApp integrado

### **🔄 EN PROCESO:**
- 🔄 Configuración de Gunicorn
- 🔄 Configuración de systemd
- 🔄 Configuración de Nginx
- 🔄 Despliegue permanente

### **⏳ PENDIENTE:**
- ⏳ Configurar SSL/HTTPS
- ⏳ Configurar monitoreo
- ⏳ Configurar backups automáticos
- ⏳ Optimizar rendimiento

---

## 🌐 **ENDPOINTS Y PUERTOS**

### **Backend Flask:**
- **Puerto**: 5000
- **URL Local**: `http://127.0.0.1:5000`
- **URL Red**: `http://10.0.0.48:5000`
- **URL Pública**: `http://149.130.160.182:5000`

### **Endpoints principales:**
- `/api/health` - Estado del sistema
- `/api/auth/login` - Autenticación
- `/api/whatsapp/*` - Endpoints WhatsApp
- `/api/candidates/*` - Gestión de candidatos
- `/api/vacancies/*` - Gestión de vacantes

---

## 📊 **LOGS Y MONITOREO**

### **Ubicaciones de logs:**
- **Gunicorn Access**: `/opt/whatsapp-backend/logs/gunicorn_access.log`
- **Gunicorn Error**: `/opt/whatsapp-backend/logs/gunicorn_error.log`
- **Aplicación**: `/opt/whatsapp-backend/app.log`

### **Comandos de monitoreo:**
```bash
# Ver logs de Gunicorn
tail -f /opt/whatsapp-backend/logs/gunicorn_error.log

# Ver estado del servicio
sudo systemctl status whatsapp-backend.service

# Ver logs del sistema
journalctl -u whatsapp-backend.service -f
```

---

## 🔧 **COMANDOS DE GESTIÓN**

### **Iniciar/Detener servicios:**
```bash
# Iniciar
sudo systemctl start whatsapp-backend.service
sudo systemctl start nginx

# Detener
sudo systemctl stop whatsapp-backend.service
sudo systemctl stop nginx

# Reiniciar
sudo systemctl restart whatsapp-backend.service
sudo systemctl restart nginx

# Estado
sudo systemctl status whatsapp-backend.service
sudo systemctl status nginx
```

### **Logs y debugging:**
```bash
# Ver logs en tiempo real
sudo journalctl -u whatsapp-backend.service -f

# Verificar configuración Nginx
sudo nginx -t

# Verificar puertos en uso
sudo netstat -tlnp | grep :5000
sudo netstat -tlnp | grep :80
```

---

## 🔐 **SEGURIDAD**

### **Firewall configurado:**
- **Puerto 22**: SSH
- **Puerto 80**: HTTP
- **Puerto 443**: HTTPS (pendiente SSL)

### **Usuarios del sistema:**
- **ubuntu**: Usuario principal
- **whatsapp_user**: Usuario de base de datos

---

## 📝 **NOTAS IMPORTANTES**

1. **Arquitectura**: ARM64 (aarch64) - importante para compatibilidad
2. **Python**: Versión 3.10.12
3. **MySQL**: Versión 8.0.43
4. **Backend**: Flask con Gunicorn
5. **Multi-tenancy**: Implementado con tabla Tenants
6. **WhatsApp**: Soporte para Business API y WhatsApp Web
7. **Autenticación**: JWT con Flask-JWT-Extended
8. **Base de datos**: MySQL con PyMySQL

---

## 🚨 **PROBLEMAS CONOCIDOS Y SOLUCIONES**

### **Error OpenAI/httpx resuelto:**
- **Problema**: Conflicto de versiones entre openai y httpx
- **Solución**: Instalar openai==1.3.7 y httpx==0.24.1

### **Error base de datos resuelto:**
- **Problema**: Tablas faltantes y foreign keys
- **Solución**: Script completo database_complete_setup.sql

### **Error usuarios resuelto:**
- **Problema**: Campo 'name' requerido
- **Solución**: ALTER TABLE Users MODIFY COLUMN name VARCHAR(255) NULL

---

## 📞 **INFORMACIÓN DE CONTACTO**

- **Proyecto**: CRM WhatsApp Backend
- **Ubicación**: Oracle Cloud Infrastructure
- **IP Pública**: 149.130.160.182
- **Estado**: Funcionando (despliegue temporal)
- **Próximo paso**: Configurar servicios permanentes (systemd + nginx + gunicorn)

---

*Documentación generada el 29 de septiembre de 2025*
*Versión del proyecto: Backend Flask + MySQL + WhatsApp Integration*
