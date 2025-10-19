# 🔐 Sistema de API Pública Multi-Tenant

## 📋 ¿Qué es esto?

Este sistema permite que cada empresa (tenant) en el CRM pueda crear sus propias **claves de API** para compartir información de forma segura con sitios web externos o aplicaciones.

---

## 🎯 ¿Para qué sirve?

Imagina que tienes un sitio web donde quieres mostrar tus vacantes de empleo. Con este sistema:

1. **Creas una API Key** desde tu CRM
2. **Usas esa clave** en tu sitio web
3. **Tu sitio web puede obtener** las vacantes automáticamente
4. **Tu sitio web puede enviar** candidatos nuevos al CRM

**Todo de forma automática y segura.**

---

## 🔧 ¿Cómo funciona?

### **Paso 1: Crear tu API Key en el CRM**

Desde tu CRM, puedes crear una API Key haciendo una petición:

```bash
POST /api/public-api-keys
Headers:
  Authorization: Bearer [tu_token_de_sesion]
  
Body:
{
  "nombre": "API Key para mi sitio web",
  "descripcion": "Usada en www.misitio.com",
  "dias_expiracion": 365
}
```

**Respuesta:**
```json
{
  "success": true,
  "api_key": "hnm_live_abc123def456...",
  "api_secret": "secret_xyz789...",
  "warning": "⚠️ Guarda el API Secret, no podrás verlo nuevamente"
}
```

**⚠️ IMPORTANTE:** Guarda el `api_key` en un lugar seguro. Es como una contraseña.

---

### **Paso 2: Ver tus API Keys**

Para ver todas tus API Keys:

```bash
GET /api/public-api-keys
Headers:
  Authorization: Bearer [tu_token_de_sesion]
```

**Respuesta:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "api_key_preview": "hnm_live_abc123...",
      "nombre_descriptivo": "API Key para mi sitio web",
      "activa": true,
      "fecha_creacion": "2025-10-19T00:00:00",
      "total_requests": 1250,
      "requests_exitosos": 1200,
      "requests_fallidos": 50
    }
  ],
  "total": 1
}
```

---

### **Paso 3: Probar tu API Key**

Para verificar que tu API Key funciona:

```bash
GET /public-api/v1/test
Headers:
  X-API-Key: hnm_live_abc123def456...
```

**Respuesta:**
```json
{
  "success": true,
  "message": "¡Tu API Key funciona correctamente!",
  "tenant_id": 1,
  "api_key_name": "API Key para mi sitio web",
  "permissions": {
    "vacancies": true,
    "candidates": true
  }
}
```

---

### **Paso 4: Ver estadísticas de uso**

Para ver cuántas veces se ha usado tu API Key:

```bash
GET /api/public-api-keys/1/stats
Headers:
  Authorization: Bearer [tu_token_de_sesion]
```

**Respuesta:**
```json
{
  "success": true,
  "stats": {
    "total_requests": 1250,
    "requests_exitosos": 1200,
    "requests_fallidos": 50,
    "avg_response_time": 150,
    "ultimo_uso": "2025-10-19T10:30:00"
  },
  "recent_logs": [
    {
      "endpoint": "/public-api/v1/test",
      "metodo": "GET",
      "status_code": 200,
      "exitoso": true,
      "ip_origen": "192.168.1.100",
      "timestamp": "2025-10-19T10:30:00"
    }
  ]
}
```

---

### **Paso 5: Desactivar una API Key**

Si necesitas desactivar temporalmente una API Key:

```bash
POST /api/public-api-keys/1/deactivate
Headers:
  Authorization: Bearer [tu_token_de_sesion]
```

---

### **Paso 6: Eliminar una API Key**

Para eliminar permanentemente una API Key:

```bash
DELETE /api/public-api-keys/1
Headers:
  Authorization: Bearer [tu_token_de_sesion]
```

---

## 🔒 Seguridad

### **¿Qué protecciones tiene?**

1. **Aislamiento por Tenant**: Cada empresa solo ve sus propias API Keys
2. **Rate Limiting**: Máximo 100 peticiones por minuto por defecto
3. **Logs de auditoría**: Se registra cada uso de la API Key
4. **Expiración**: Puedes configurar que la API Key expire automáticamente
5. **Desactivación**: Puedes desactivar una API Key en cualquier momento
6. **Hash seguro**: Los secretos se guardan encriptados con bcrypt

### **¿Qué información se registra?**

Cada vez que alguien usa tu API Key, se registra:
- Qué endpoint accedió
- Desde qué IP
- Si fue exitoso o falló
- Cuánto tiempo tardó
- Fecha y hora

---

## 📊 Límites

| Límite | Valor por defecto | Configurable |
|--------|-------------------|--------------|
| Peticiones por minuto | 100 | ✅ Sí |
| Peticiones por día | 10,000 | ✅ Sí |
| Tamaño de archivo CV | 10 MB | ❌ No |

---

## 🚀 Ejemplo de uso en un sitio web

### **En tu sitio web (JavaScript):**

```javascript
// Configurar tu API Key
const API_KEY = 'hnm_live_abc123def456...';
const API_URL = 'https://tu-crm.com';

// Hacer una petición de prueba
fetch(`${API_URL}/public-api/v1/test`, {
  headers: {
    'X-API-Key': API_KEY
  }
})
.then(response => response.json())
.then(data => {
  console.log('API Key válida:', data);
})
.catch(error => {
  console.error('Error:', error);
});
```

---

## ❓ Preguntas Frecuentes

### **¿Puedo tener múltiples API Keys?**
Sí, puedes crear tantas como necesites. Por ejemplo, una para tu sitio web y otra para tu app móvil.

### **¿Qué pasa si alguien roba mi API Key?**
Puedes desactivarla o eliminarla inmediatamente desde el CRM. También puedes ver en los logs quién la está usando.

### **¿Puedo cambiar los límites de peticiones?**
Sí, al crear la API Key puedes especificar límites personalizados.

### **¿Las API Keys expiran?**
Solo si lo configuras. Puedes crear API Keys sin fecha de expiración o con una fecha específica.

### **¿Puedo ver el secreto de una API Key después de crearla?**
No, por seguridad el secreto solo se muestra una vez al crear la API Key. Si lo pierdes, debes crear una nueva.

---

## 🎓 Resumen Simple

**Para el administrador del CRM:**
1. Entras al CRM
2. Creas una API Key con un nombre descriptivo
3. Copias la clave generada
4. La usas en tu sitio web o aplicación
5. Puedes ver estadísticas de uso en cualquier momento

**Para el sitio web:**
1. Recibe la API Key del administrador
2. La incluye en el header `X-API-Key` de cada petición
3. Puede obtener vacantes y enviar candidatos
4. Todo funciona automáticamente

---

## 📞 Soporte

Si tienes problemas:
1. Verifica que la API Key esté activa
2. Revisa los logs de uso para ver errores
3. Verifica que no hayas excedido el rate limit
4. Contacta al administrador del sistema

---

## 🔄 Próximos pasos

Una vez que tengas tu API Key funcionando, podrás:
- ✅ Obtener vacantes (próximamente)
- ✅ Registrar candidatos (próximamente)
- ✅ Ver estadísticas en tiempo real

---

**¡Listo! Tu sistema de API está configurado y funcionando de forma segura.**
