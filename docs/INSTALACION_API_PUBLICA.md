# 🚀 Guía de Instalación - Sistema de API Pública

## ✅ Requisitos previos

- MySQL/MariaDB funcionando
- Python 3.8 o superior
- Librería `bcrypt` instalada

---

## 📦 Paso 1: Instalar dependencias

```bash
pip install bcrypt
```

---

## 🗄️ Paso 2: Ejecutar migración de base de datos

Ejecuta el script SQL para crear las tablas necesarias:

```bash
mysql -u tu_usuario -p tu_base_de_datos < migrations/create_public_api_keys.sql
```

O desde MySQL Workbench / phpMyAdmin:
1. Abre el archivo `migrations/create_public_api_keys.sql`
2. Copia todo el contenido
3. Pégalo en tu cliente SQL
4. Ejecuta

---

## ✅ Paso 3: Verificar instalación

Verifica que las tablas se crearon correctamente:

```sql
SHOW TABLES LIKE '%API%';
```

Deberías ver:
- `Tenant_API_Keys`
- `API_Key_Logs`
- `API_Key_Rate_Limits`
- `API_Endpoints_Disponibles`

---

## 🔄 Paso 4: Reiniciar el servidor

```bash
# Detener el servidor si está corriendo
# Ctrl + C

# Iniciar nuevamente
python app.py
```

---

## 🧪 Paso 5: Probar el sistema

### **5.1 Crear una API Key de prueba**

Desde Postman o curl:

```bash
curl -X POST http://localhost:5000/api/public-api-keys \
  -H "Authorization: Bearer TU_TOKEN_DE_SESION" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "API Key de Prueba",
    "descripcion": "Para testing"
  }'
```

**Respuesta esperada:**
```json
{
  "success": true,
  "api_key": "hnm_live_...",
  "api_secret": "...",
  "warning": "⚠️ IMPORTANTE: Guarda el API Secret..."
}
```

**⚠️ COPIA Y GUARDA** el `api_key` que te devuelve.

---

### **5.2 Probar la API Key**

```bash
curl -X GET http://localhost:5000/public-api/v1/test \
  -H "X-API-Key: hnm_live_TU_API_KEY_AQUI"
```

**Respuesta esperada:**
```json
{
  "success": true,
  "message": "¡Tu API Key funciona correctamente!",
  "tenant_id": 1,
  "api_key_name": "API Key de Prueba"
}
```

---

### **5.3 Ver tus API Keys**

```bash
curl -X GET http://localhost:5000/api/public-api-keys \
  -H "Authorization: Bearer TU_TOKEN_DE_SESION"
```

---

## 🎉 ¡Listo!

Si todos los pasos anteriores funcionaron, tu sistema de API está instalado correctamente.

---

## 🔧 Solución de problemas

### **Error: "Module 'bcrypt' not found"**
```bash
pip install bcrypt
```

### **Error: "Table already exists"**
Las tablas ya están creadas. Puedes continuar.

### **Error: "API Key inválida"**
Verifica que:
1. Copiaste la API Key completa
2. La API Key está activa en la base de datos
3. No ha expirado

### **Error: "Rate limit excedido"**
Espera 1 minuto o aumenta el límite en la base de datos:
```sql
UPDATE Tenant_API_Keys 
SET rate_limit_per_minute = 200 
WHERE id = TU_API_KEY_ID;
```

---

## 📊 Verificar en la base de datos

```sql
-- Ver todas las API Keys
SELECT 
    id, 
    tenant_id, 
    LEFT(api_key, 20) as api_key_preview,
    nombre_descriptivo,
    activa,
    fecha_creacion,
    total_requests
FROM Tenant_API_Keys;

-- Ver logs recientes
SELECT 
    endpoint,
    metodo,
    status_code,
    exitoso,
    timestamp
FROM API_Key_Logs
ORDER BY timestamp DESC
LIMIT 10;
```

---

## 🔄 Mantenimiento

### **Limpiar logs antiguos (ejecutar mensualmente)**

```sql
CALL cleanup_api_logs(90);  -- Eliminar logs de más de 90 días
```

### **Ver estadísticas de una API Key**

```sql
CALL get_api_key_stats(1);  -- Reemplaza 1 con el ID de tu API Key
```

---

## 📝 Próximos pasos

Ahora que el sistema está instalado:

1. ✅ Crea API Keys para tus tenants
2. ✅ Configura los endpoints de vacantes y candidatos (próximamente)
3. ✅ Integra con tu sitio web

---

## 🆘 ¿Necesitas ayuda?

Revisa:
- `PUBLIC_API_DOCUMENTATION.md` - Documentación completa
- Logs del servidor: `app.log`
- Logs de la base de datos: tabla `API_Key_Logs`
