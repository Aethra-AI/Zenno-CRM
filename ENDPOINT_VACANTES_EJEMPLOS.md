# 📋 Endpoint de Vacantes Públicas - Guía de Uso

## 🎯 Endpoint Principal

```
GET /public-api/v1/vacancies
```

Este endpoint permite obtener las vacantes activas de tu empresa sin exponer información sensible.

---

## 🔑 Autenticación

Todas las peticiones requieren tu API Key en el header:

```bash
X-API-Key: hnm_live_abc123def456...
```

---

## 📊 Ejemplo 1: Obtener todas las vacantes

### **Petición:**
```bash
curl -X GET "http://localhost:5000/public-api/v1/vacancies" \
  -H "X-API-Key: hnm_live_abc123def456..."
```

### **Respuesta:**
```json
{
  "success": true,
  "data": [
    {
      "id": "vac_123",
      "cargo": "Desarrollador Full Stack",
      "descripcion": "Buscamos desarrollador con experiencia en tecnologías web modernas para unirse a nuestro equipo.",
      "requisitos": [
        "3+ años de experiencia en desarrollo web",
        "Dominio de React y Node.js",
        "Inglés intermedio",
        "Disponibilidad inmediata"
      ],
      "salario": {
        "min": 25000,
        "max": 35000,
        "moneda": "HNL"
      },
      "ciudad": "Tegucigalpa",
      "estado": "Abierta",
      "fecha_publicacion": "2025-10-15",
      "fecha_cierre": "2025-11-15",
      "dias_restantes": 27
    },
    {
      "id": "vac_124",
      "cargo": "Diseñador UX/UI",
      "descripcion": "Diseñador creativo para proyectos digitales innovadores.",
      "requisitos": [
        "Portfolio demostrable",
        "Figma y Adobe XD",
        "Experiencia en diseño responsive"
      ],
      "salario": {
        "monto": 20000,
        "moneda": "HNL"
      },
      "ciudad": "San Pedro Sula",
      "estado": "Abierta",
      "fecha_publicacion": "2025-10-18",
      "fecha_cierre": null,
      "dias_restantes": null
    }
  ],
  "pagination": {
    "total": 15,
    "limit": 50,
    "offset": 0,
    "current_page": 1,
    "total_pages": 1,
    "has_more": false
  },
  "filters_applied": {
    "estado": "Abierta",
    "ciudad": null
  }
}
```

---

## 📍 Ejemplo 2: Filtrar por ciudad

### **Petición:**
```bash
curl -X GET "http://localhost:5000/public-api/v1/vacancies?ciudad=Tegucigalpa" \
  -H "X-API-Key: hnm_live_abc123def456..."
```

### **Respuesta:**
```json
{
  "success": true,
  "data": [
    {
      "id": "vac_123",
      "cargo": "Desarrollador Full Stack",
      "ciudad": "Tegucigalpa",
      ...
    }
  ],
  "pagination": {
    "total": 5,
    ...
  },
  "filters_applied": {
    "estado": "Abierta",
    "ciudad": "Tegucigalpa"
  }
}
```

---

## 📄 Ejemplo 3: Paginación

Para obtener resultados en páginas:

### **Página 1 (primeros 10 resultados):**
```bash
curl -X GET "http://localhost:5000/public-api/v1/vacancies?limit=10&offset=0" \
  -H "X-API-Key: hnm_live_abc123def456..."
```

### **Página 2 (siguientes 10 resultados):**
```bash
curl -X GET "http://localhost:5000/public-api/v1/vacancies?limit=10&offset=10" \
  -H "X-API-Key: hnm_live_abc123def456..."
```

### **Respuesta con paginación:**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "total": 25,
    "limit": 10,
    "offset": 0,
    "current_page": 1,
    "total_pages": 3,
    "has_more": true
  }
}
```

---

## 🏙️ Ejemplo 4: Obtener lista de ciudades

Útil para crear filtros dinámicos en tu sitio web:

### **Petición:**
```bash
curl -X GET "http://localhost:5000/public-api/v1/vacancies/cities" \
  -H "X-API-Key: hnm_live_abc123def456..."
```

### **Respuesta:**
```json
{
  "success": true,
  "data": [
    {
      "ciudad": "Tegucigalpa",
      "total_vacantes": 8
    },
    {
      "ciudad": "San Pedro Sula",
      "total_vacantes": 5
    },
    {
      "ciudad": "La Ceiba",
      "total_vacantes": 2
    }
  ]
}
```

---

## 🔧 Parámetros de Consulta

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `estado` | string | "Abierta" | Estado de la vacante |
| `ciudad` | string | null | Filtrar por ciudad específica |
| `limit` | integer | 50 | Número de resultados (máx: 100) |
| `offset` | integer | 0 | Offset para paginación |

---

## 📦 Estructura de Respuesta

### **Campos de cada vacante:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | string | ID ofuscado de la vacante (ej: "vac_123") |
| `cargo` | string | Título del puesto |
| `descripcion` | string | Descripción completa de la vacante |
| `requisitos` | array | Lista de requisitos |
| `salario` | object/null | Información salarial |
| `ciudad` | string | Ciudad donde se ubica la vacante |
| `estado` | string | Estado actual (siempre "Abierta" en API pública) |
| `fecha_publicacion` | string | Fecha de publicación (ISO 8601) |
| `fecha_cierre` | string/null | Fecha de cierre (ISO 8601) |
| `dias_restantes` | integer/null | Días restantes hasta el cierre |

### **Formato de salario:**

**Opción 1: Rango salarial**
```json
{
  "min": 25000,
  "max": 35000,
  "moneda": "HNL"
}
```

**Opción 2: Salario fijo**
```json
{
  "monto": 20000,
  "moneda": "HNL"
}
```

**Opción 3: Sin información salarial**
```json
null
```

---

## 🚫 Errores Comunes

### **Error 401: API Key inválida**
```json
{
  "success": false,
  "error": "API Key inválida"
}
```
**Solución:** Verifica que tu API Key sea correcta y esté activa.

---

### **Error 403: Sin permisos**
```json
{
  "success": false,
  "error": "Esta API Key no tiene permisos para acceder a vacantes",
  "code": "PERMISSION_DENIED"
}
```
**Solución:** Tu API Key no tiene el permiso `vacancies: true`. Contacta al administrador.

---

### **Error 429: Rate limit excedido**
```json
{
  "success": false,
  "error": "Rate limit excedido",
  "message": "Has excedido el límite de 100 peticiones por minuto"
}
```
**Solución:** Espera 1 minuto antes de hacer más peticiones.

---

### **Error 400: Parámetros inválidos**
```json
{
  "success": false,
  "error": "Parámetros inválidos",
  "message": "Los parámetros limit y offset deben ser números enteros"
}
```
**Solución:** Verifica que `limit` y `offset` sean números válidos.

---

## 💻 Ejemplo de Integración en JavaScript

### **Función para obtener vacantes:**

```javascript
async function obtenerVacantes(ciudad = null, pagina = 1) {
  const API_KEY = 'hnm_live_abc123def456...';
  const API_URL = 'http://localhost:5000';
  const LIMIT = 10;
  const offset = (pagina - 1) * LIMIT;
  
  // Construir URL con parámetros
  let url = `${API_URL}/public-api/v1/vacancies?limit=${LIMIT}&offset=${offset}`;
  if (ciudad) {
    url += `&ciudad=${encodeURIComponent(ciudad)}`;
  }
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'X-API-Key': API_KEY
      }
    });
    
    if (!response.ok) {
      throw new Error(`Error HTTP: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data.success) {
      return {
        vacantes: data.data,
        paginacion: data.pagination
      };
    } else {
      throw new Error(data.error);
    }
    
  } catch (error) {
    console.error('Error obteniendo vacantes:', error);
    throw error;
  }
}

// Uso:
obtenerVacantes('Tegucigalpa', 1)
  .then(resultado => {
    console.log('Vacantes:', resultado.vacantes);
    console.log('Total:', resultado.paginacion.total);
  })
  .catch(error => {
    console.error('Error:', error);
  });
```

---

### **Función para obtener ciudades:**

```javascript
async function obtenerCiudades() {
  const API_KEY = 'hnm_live_abc123def456...';
  const API_URL = 'http://localhost:5000';
  
  try {
    const response = await fetch(`${API_URL}/public-api/v1/vacancies/cities`, {
      method: 'GET',
      headers: {
        'X-API-Key': API_KEY
      }
    });
    
    const data = await response.json();
    
    if (data.success) {
      return data.data;
    } else {
      throw new Error(data.error);
    }
    
  } catch (error) {
    console.error('Error obteniendo ciudades:', error);
    throw error;
  }
}

// Uso:
obtenerCiudades()
  .then(ciudades => {
    ciudades.forEach(ciudad => {
      console.log(`${ciudad.ciudad}: ${ciudad.total_vacantes} vacantes`);
    });
  });
```

---

## 🔒 Información de Seguridad

### **¿Qué NO se expone?**
- ❌ Nombre de la empresa cliente
- ❌ ID del cliente
- ❌ Información de contacto de la empresa
- ❌ Email o teléfono de la empresa
- ❌ Usuario que creó la vacante
- ❌ Tenant ID

### **¿Qué SÍ se comparte?**
- ✅ Cargo solicitado
- ✅ Descripción de la vacante
- ✅ Requisitos
- ✅ Rango salarial (si está configurado)
- ✅ Ciudad
- ✅ Fechas de publicación y cierre

---

## 📊 Límites y Restricciones

| Límite | Valor |
|--------|-------|
| Peticiones por minuto | 100 |
| Resultados máximos por petición | 100 |
| Resultados por defecto | 50 |
| Solo vacantes con estado | "Abierta" |
| Solo vacantes no vencidas | Sí |

---

## 🎓 Buenas Prácticas

1. **Cachea los resultados** en tu sitio web para reducir peticiones
2. **Usa paginación** para mejorar el rendimiento
3. **Maneja errores** apropiadamente
4. **Implementa retry logic** para peticiones fallidas
5. **Guarda la API Key** en variables de entorno, no en el código
6. **Monitorea el uso** desde el panel del CRM

---

## 🆘 Soporte

Si tienes problemas:
1. Verifica que tu API Key esté activa
2. Revisa los logs en el CRM
3. Verifica los límites de rate limiting
4. Contacta al administrador del sistema

---

**¡Listo para integrar en tu sitio web!** 🚀
