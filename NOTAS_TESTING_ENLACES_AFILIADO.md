# 🧪 GUÍA DE PRUEBAS - SISTEMA DE ENLACES DE AFILIADO

## ✅ CÓDIGO LISTO PARA PRUEBAS

El sistema está completamente funcional usando solo la tabla `TrackingEnlaces` para el tracking de usuarios.

---

## 📋 CHECKLIST PRE-PRUEBAS

### ✅ Tabla TrackingEnlaces Existe
La tabla ya existe en tu BD con la estructura correcta:
```sql
CREATE TABLE IF NOT EXISTS TrackingEnlaces (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tenant_id INT NOT NULL,
  user_id INT NOT NULL,
  candidato_id INT NULL,
  codigo_referencia VARCHAR(20) NOT NULL,
  enlace_usado VARCHAR(500) NOT NULL,
  ip_address VARCHAR(45),
  user_agent TEXT,
  estado ENUM('click','registrado','contratado') DEFAULT 'click',
  fecha_click TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  fecha_registro TIMESTAMP NULL,
  INDEX idx_tenant_user (tenant_id, user_id),
  INDEX idx_codigo_ref (codigo_referencia),
  FOREIGN KEY (tenant_id) REFERENCES Tenants(id),
  FOREIGN KEY (user_id) REFERENCES Users(id),
  FOREIGN KEY (candidato_id) REFERENCES Afiliados(id_afiliado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### ✅ Endpoints Backend Funcionales
- `POST /api/users/{user_id}/affiliate-link` - Crear enlace
- `GET /api/users/{user_id}/affiliate-links` - Listar enlaces
- `POST /public-api/v1/candidates` - Registrar candidato (modificado)

### ✅ Frontend Web Captura Código
- Página captura `?ref=` de la URL
- Guarda en localStorage
- Envía al backend

### ✅ Frontend CRM Tiene Botón
- Botón "Crear Enlace de Afiliado" en menú de usuarios
- Modal para mostrar y copiar enlace

---

## 🧪 PRUEBA 1: CREAR ENLACE DESDE CRM

### Paso 1: Iniciar Sesión en CRM
```
URL: http://localhost:3000
Usuario: cualquier usuario (admin, supervisor o reclutador)
```

### Paso 2: Ir a Pestaña Usuarios
- Click en "Usuarios" en el menú lateral
- Se debe mostrar la lista de usuarios

### Paso 3: Crear Enlace
- Click en menú (3 puntos) de cualquier usuario
- Seleccionar "Crear Enlace de Afiliado"
- Modal debe mostrar el enlace generado
- Click en "Copiar Enlace"

**Resultado esperado:**
```json
{
  "success": true,
  "codigo_referencia": "ABC123XYZ789",
  "url": "https://henmir-hn.github.io/portal-empleo-henmir/?ref=ABC123XYZ789"
}
```

**Verificar en BD:**
```sql
SELECT * FROM TrackingEnlaces 
WHERE codigo_referencia = 'ABC123XYZ789'
ORDER BY fecha_click DESC
LIMIT 1;

-- Debe mostrar:
-- estado: "click"
-- user_id: [ID del usuario]
-- candidato_id: NULL
```

---

## 🧪 PRUEBA 2: CANDIDATO USA EL ENLACE

### Paso 1: Abrir Enlace Generado
```
URL: https://henmir-hn.github.io/portal-empleo-henmir/?ref=ABC123XYZ789
```

### Paso 2: Verificar Consola del Navegador
- Abrir DevTools (F12)
- En Console debe aparecer:
  ```
  Código de referencia capturado: ABC123XYZ789
  ```

### Paso 3: Ir a Formulario de Registro
- Click en "Registrarse" o ir a `#/registrarse`
- El código debe estar guardado en localStorage

---

## 🧪 PRUEBA 3: REGISTRO DE CANDIDATO

### Paso 1: Completar Formulario
```
Nombre: "Juan Pérez"
Apellido: "García"
Identidad: "0801-1990-12345"
Email: "juan.perez@test.com"
Teléfono: "+504 9999-9999"
Ciudad: "Tegucigalpa"
Profesión: "Desarrollador Full Stack"
Educación: "Universitario"
CV: [subir cualquier PDF]
```

### Paso 2: Aceptar Términos y Enviar
- Marcar checkbox de términos
- Click en "Completar Registro"

**Resultado esperado:**
- Mensaje de éxito
- Formulario se limpia

**Verificar en Consola:**
```
Enviando código de referencia: ABC123XYZ789
```

---

## 🧪 PRUEBA 4: VERIFICAR EN BASE DE DATOS

### Verificar TrackingEnlaces

```sql
-- Ver registro con estado 'registrado'
SELECT 
    t.id,
    t.user_id,
    t.candidato_id,
    t.codigo_referencia,
    t.estado,
    t.fecha_click,
    t.fecha_registro,
    t.ip_address,
    u.nombre as usuario_referente
FROM TrackingEnlaces t
JOIN Users u ON t.user_id = u.id
WHERE t.codigo_referencia = 'ABC123XYZ789'
ORDER BY t.fecha_registro DESC;

-- Debe mostrar DOS filas:
-- Fila 1: estado='click' (creación del enlace)
-- Fila 2: estado='registrado', candidato_id=[ID], fecha_registro=[fecha]
```

### Verificar Candidato en Afiliados

```sql
-- Ver candidato creado
SELECT 
    a.id_afiliado,
    a.nombre_completo,
    a.email,
    a.fuente_reclutamiento,
    a.fecha_registro
FROM Afiliados a
WHERE a.identidad = '0801-1990-12345'
LIMIT 1;

-- Debe mostrar:
-- nombre_completo: "Juan Pérez García"
-- fuente_reclutamiento: "Sitio Web"
```

### Relacionar Candidato con Usuario

```sql
-- Ver candidato + usuario que lo trajo
SELECT 
    a.id_afiliado,
    a.nombre_completo,
    a.email,
    a.fecha_registro,
    t.user_id,
    t.codigo_referencia,
    t.estado,
    u.nombre as referido_por
FROM Afiliados a
JOIN TrackingEnlaces t ON a.id_afiliado = t.candidato_id
JOIN Users u ON t.user_id = u.id
WHERE t.codigo_referencia = 'ABC123XYZ789'
  AND t.estado = 'registrado'
LIMIT 1;

-- Debe mostrar la relación completa
```

---

## 🧪 PRUEBA 5: LISTAR ENLACES DEL USUARIO

### Desde CRM
```bash
curl -X GET http://localhost:5000/api/users/5/affiliate-links \
  -H "Authorization: Bearer {token}"
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": [
    {
      "codigo_referencia": "ABC123XYZ789",
      "enlace_usado": "https://henmir-hn.github.io/portal-empleo-henmir/?ref=ABC123XYZ789",
      "estado": "click",
      "fecha_click": "2025-01-20 09:00:00",
      "fecha_registro": "2025-01-20 10:30:00",
      "total_registrados": 1
    }
  ]
}
```

---

## 🐛 POSIBLES ERRORES Y SOLUCIONES

### Error: "Field 'created_by' doesn't exist"
**Solución:** Ya corregido. El código ya NO usa `created_by` en Afiliados.

### Error: "candidato_id cannot be null"
**Solución:** Verificar que el candidato se creó correctamente antes de insertar en TrackingEnlaces.

### Error: "codigo_referencia" no encuentra usuario
**Solución:** 
```sql
-- Verificar que existe el código
SELECT * FROM TrackingEnlaces WHERE codigo_referencia = 'ABC123XYZ789';
```

### El enlace no copia al portapapeles
**Solución:** Verificar que el navegador permite acceso al clipboard. Chrome debe tener permisos.

### El candidato no aparece para el usuario
**Solución:** 
```sql
-- Verificar relación en TrackingEnlaces
SELECT 
    t.user_id,
    t.candidato_id,
    t.estado
FROM TrackingEnlaces t
WHERE t.candidato_id IS NOT NULL
ORDER BY t.fecha_registro DESC
LIMIT 5;
```

---

## ✅ ÉXITO = TODO FUNCIONA SI...

1. ✅ Enlace se crea desde CRM
2. ✅ Modal muestra la URL correcta
3. ✅ Enlace se puede copiar
4. ✅ Candidato ve el formulario con parámetro `?ref=`
5. ✅ Candidato se registra exitosamente
6. ✅ Se crean 2 registros en TrackingEnlaces (click + registrado)
7. ✅ Candidato tiene candidato_id en TrackingEnlaces
8. ✅ Se puede ver la relación entre usuario y candidato

---

## 📊 MÉTRICAS DE PRUEBA

### Candidatos por Usuario
```sql
SELECT 
    u.id,
    u.nombre,
    COUNT(DISTINCT t.candidato_id) as total_candidatos
FROM Users u
LEFT JOIN TrackingEnlaces t ON u.id = t.user_id 
    AND t.estado = 'registrado'
GROUP BY u.id, u.nombre
ORDER BY total_candidatos DESC;
```

### Enlaces más Efectivos
```sql
SELECT 
    codigo_referencia,
    COUNT(DISTINCT candidato_id) as total_registros,
    MIN(fecha_registro) as primera_conversion
FROM TrackingEnlaces
WHERE estado = 'registrado'
GROUP BY codigo_referencia
ORDER BY total_registros DESC;
```

---

**¡Listo para probar!** 🚀
