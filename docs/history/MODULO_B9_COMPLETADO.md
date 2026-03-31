# ✅ MÓDULO B9 - ENDPOINTS DE CLIENTES COMPLETADO

**Fecha:** Octubre 9, 2025  
**Archivo modificado:** `bACKEND/app.py`  
**Estado:** 🟢 Listo para probar

---

## 📋 CAMBIOS REALIZADOS

### **1. Modificación de GET `/api/clients`** ✅

**Ubicación:** Línea 6536-6576

**Cambios:**
- ✅ Filtrado por usuario según rol usando `c.created_by_user` (directo)
- ✅ Incluye clientes antiguos sin `created_by_user` (NULL)

**Antes:**
```python
cursor.execute("""
    SELECT c.*, COUNT(DISTINCT v.id_vacante) as vacantes_count
    FROM Clientes c
    LEFT JOIN Vacantes v ON ...
    WHERE c.tenant_id = %s
    GROUP BY c.id_cliente
""", (tenant_id,))
# Todos los usuarios ven TODOS los clientes
```

**Después:**
```python
user_id = g.current_user['user_id']

query = """..."""
params = [tenant_id, tenant_id]

# 🔐 MÓDULO B9: Filtrar por usuario según rol
condition, filter_params = build_user_filter_condition(user_id, tenant_id, 'c.created_by_user')
if condition:
    query += f" AND ({condition} OR c.created_by_user IS NULL)"
    params.extend(filter_params)

cursor.execute(query, tuple(params))
```

**Resultado:**
- Admin: Ve TODOS los clientes
- Supervisor: Ve clientes creados por él y su equipo
- Reclutador: Solo ve clientes que creó

---

### **2. Modificación de POST `/api/clients`** ✅

**Ubicación:** Línea 6577-6625

**Cambios:**
- ✅ Verifica permiso con `can_create_resource()`
- ✅ Agrega `created_by_user` al INSERT
- ✅ Log de intentos sin permiso

**Código agregado:**
```python
# 🔐 MÓDULO B9: Verificar permiso de creación
if not can_create_resource(user_id, tenant_id, 'client'):
    app.logger.warning(f"Usuario {user_id} intentó crear cliente sin permisos")
    return jsonify({'error': 'No tienes permisos para crear clientes'}), 403

# 🔐 MÓDULO B9: Insertar con created_by_user
sql = """
    INSERT INTO Clientes (
        empresa, contacto_nombre, telefono, email, sector, observaciones, tenant_id, created_by_user
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""
cursor.execute(sql, (..., tenant_id, user_id))
```

---

### **3. Modificación de DELETE `/api/clients/<id>`** ✅

**Ubicación:** Línea 6638-6657

**Cambios:**
- ✅ Verifica acceso con `can_access_resource()` (requiere 'full')
- ✅ Log de intentos sin permiso
- ✅ Retorna 403 si no tiene acceso

**Código agregado:**
```python
# 🔐 MÓDULO B9: Verificar acceso de eliminación
if not can_access_resource(user_id, tenant_id, 'client', client_id, 'full'):
    app.logger.warning(f"Usuario {user_id} intentó eliminar cliente {client_id} sin permisos")
    return jsonify({
        'success': False,
        'error': 'No tienes permisos para eliminar este cliente',
        'code': 'FORBIDDEN'
    }), 403
```

---

### **4. Modificación de GET `/api/clients/<id>/metrics`** ✅

**Ubicación:** Línea 6698-6723

**Cambios:**
- ✅ Verifica acceso de lectura con `can_access_resource()`
- ✅ Log de intentos sin permiso

**Código agregado:**
```python
# 🔐 MÓDULO B9: Verificar acceso de lectura
if not can_access_resource(user_id, tenant_id, 'client', client_id, 'read'):
    app.logger.warning(f"Usuario {user_id} intentó acceder a métricas de cliente {client_id} sin permisos")
    return jsonify({'error': 'No tienes acceso a este cliente'}), 403
```

---

### **5. Modificación de GET `/api/clients/<id>/vacancies`** ✅

**Ubicación:** Línea 8662-8707

**Cambios:**
- ✅ Verifica acceso de lectura al cliente
- ✅ Agrega `tenant_id` al query de vacantes
- ✅ Log de intentos sin permiso

**Código agregado:**
```python
# 🔐 MÓDULO B9: Verificar acceso de lectura al cliente
if not can_access_resource(user_id, tenant_id, 'client', client_id, 'read'):
    return jsonify({'error': 'No tienes acceso a este cliente'}), 403

# Query con tenant_id
WHERE v.id_cliente = %s AND v.tenant_id = %s
```

---

### **6. Modificación de GET `/api/clients/<id>/applications`** ✅

**Ubicación:** Línea 8719-8773

**Cambios:**
- ✅ Verifica acceso de lectura al cliente
- ✅ Agrega `tenant_id` al query
- ✅ Log de intentos sin permiso

---

### **7. Modificación de GET `/api/clients/<id>/hired-candidates`** ✅

**Ubicación:** Línea 8775-8824

**Cambios:**
- ✅ Verifica acceso de lectura al cliente
- ✅ Log de intentos sin permiso

---

## 🔑 CONCEPTO CLAVE: CLIENTES CON created_by_user DIRECTO

A diferencia de postulaciones y entrevistas, los clientes tienen su propia columna `created_by_user`:

```
Cliente A (created_by_user: 8)
  ├── Vacante 1 ✅ Reclutador 8 puede verla
  ├── Vacante 2 ✅ Reclutador 8 puede ver métricas
  └── Vacante 3 ✅ Reclutador 8 puede ver contratados

Cliente B (created_by_user: 10)
  ├── Vacante 4 ❌ Reclutador 8 NO tiene acceso
  └── ...        ❌ Reclutador 8 NO puede ver nada de este cliente
```

---

## 📊 MATRIZ DE PERMISOS APLICADA

| Acción | Admin | Supervisor<br>(equipo [8,12]) | Reclutador<br>(ID 8) |
|--------|-------|-------------------------------|----------------------|
| **Ver todos los clientes** | ✅ | ❌ | ❌ |
| **Ver clientes del equipo** | ✅ | ✅ (5, 8, 12) | ❌ |
| **Ver clientes propios** | ✅ | ✅ | ✅ (solo 8) |
| **Crear cliente** | ✅ | ✅ | ✅ |
| **Ver métricas cliente propio** | ✅ | ✅ | ✅ |
| **Ver métricas cliente equipo** | ✅ | ✅ | ❌ (403) |
| **Ver vacantes cliente propio** | ✅ | ✅ | ✅ |
| **Ver vacantes cliente ajeno** | ✅ | ✅ (equipo) | ❌ (403) |
| **Eliminar cliente propio** | ✅ | ✅ | ✅ |
| **Eliminar cliente ajeno** | ✅ | ❌ (403) | ❌ (403) |

---

## 🧪 CASOS DE PRUEBA

### **Test 1: Admin ve todos los clientes**

**Request:**
```http
GET /api/clients
Authorization: Bearer <token_admin>
```

**Query esperada:**
```sql
SELECT c.*, COUNT(DISTINCT v.id_vacante) as vacantes_count
FROM Clientes c
LEFT JOIN Vacantes v ON c.id_cliente = v.id_cliente AND v.tenant_id = 1
WHERE c.tenant_id = 1
-- Sin filtro adicional por usuario
GROUP BY c.id_cliente
```

**Resultado:** Todos los clientes del tenant

---

### **Test 2: Supervisor ve clientes de su equipo**

**Request:**
```http
GET /api/clients
Authorization: Bearer <token_supervisor_5>
```

**Query esperada:**
```sql
WHERE c.tenant_id = 1
AND (c.created_by_user IN (5, 8, 12) OR c.created_by_user IS NULL)
```

**Resultado:**
- ✅ Cliente A (created_by_user: 5) - suyo
- ✅ Cliente B (created_by_user: 8) - equipo
- ✅ Cliente C (created_by_user: 12) - equipo
- ✅ Cliente D (created_by_user: NULL) - antiguo
- ❌ Cliente E (created_by_user: 10) - ajeno

---

### **Test 3: Reclutador solo ve sus clientes**

**Request:**
```http
GET /api/clients
Authorization: Bearer <token_reclutador_8>
```

**Query esperada:**
```sql
WHERE c.tenant_id = 1
AND (c.created_by_user = 8 OR c.created_by_user IS NULL)
```

**Resultado:**
- ✅ Cliente B (created_by_user: 8) - suyo
- ✅ Cliente D (created_by_user: NULL) - antiguo
- ❌ Cliente A, C, E - ajenos

---

### **Test 4: Crear cliente registra created_by_user**

**Request:**
```http
POST /api/clients
Authorization: Bearer <token_reclutador_8>
Content-Type: application/json

{
  "empresa": "Tech Solutions SA",
  "contacto_nombre": "Roberto Pérez",
  "telefono": "99887766",
  "email": "contacto@techsolutions.com",
  "sector": "Tecnología",
  "observaciones": "Cliente potencial"
}
```

**Query esperada:**
```sql
INSERT INTO Clientes (
  empresa, contacto_nombre, telefono, email, sector, observaciones, tenant_id, created_by_user
) VALUES (
  'Tech Solutions SA', 'Roberto Pérez', '99887766', 'contacto@techsolutions.com', 
  'Tecnología', 'Cliente potencial', 1, 8
)
```

**Resultado esperado:**
```json
{
  "success": true,
  "message": "Cliente agregado."
}
```

---

### **Test 5: Acceso a métricas denegado**

**Request:**
```http
GET /api/clients/10/metrics
Authorization: Bearer <token_reclutador_8>
```

**Escenario:** Reclutador 8 intenta ver métricas de cliente creado por Reclutador 10

**Resultado esperado:**
```json
{
  "error": "No tienes acceso a este cliente",
  "code": "FORBIDDEN"
}
```

**Código HTTP:** `403 Forbidden`

---

### **Test 6: Acceso a vacantes de cliente denegado**

**Request:**
```http
GET /api/clients/10/vacancies
Authorization: Bearer <token_reclutador_8>
```

**Resultado esperado:**
```json
{
  "error": "No tienes acceso a este cliente",
  "code": "FORBIDDEN"
}
```

---

## 🔍 VALIDACIÓN DE LOGS

### **Logs de creación exitosa:**
```
INFO - Usuario 8 creando cliente: Tech Solutions SA
INFO - Cliente creado exitosamente: ID 15
```

### **Logs de intentos sin permiso:**
```
WARNING - Usuario 10 intentó crear cliente sin permisos
WARNING - Usuario 8 intentó eliminar cliente 10 sin permisos
WARNING - Usuario 8 intentó acceder a métricas de cliente 10 sin permisos
WARNING - Usuario 8 intentó acceder a vacantes de cliente 10 sin permisos
WARNING - Usuario 8 intentó acceder a postulaciones de cliente 10 sin permisos
WARNING - Usuario 8 intentó acceder a contratados de cliente 10 sin permisos
```

---

## ✅ CHECKLIST DE VALIDACIÓN

### **Funcionalidad:**
- [x] `GET /api/clients` filtra por usuario según rol
- [x] `POST /api/clients` valida permisos y registra `created_by_user`
- [x] `DELETE /api/clients/<id>` valida acceso (requiere 'full')
- [x] `GET /api/clients/<id>/metrics` valida acceso (requiere 'read')
- [x] `GET /api/clients/<id>/vacancies` valida acceso (requiere 'read')
- [x] `GET /api/clients/<id>/applications` valida acceso (requiere 'read')
- [x] `GET /api/clients/<id>/hired-candidates` valida acceso (requiere 'read')

### **Seguridad:**
- [x] Reclutador NO puede ver clientes de otros
- [x] Supervisor puede ver clientes de su equipo
- [x] Admin puede ver todos los clientes
- [x] Retorna 403 en accesos no autorizados
- [x] Logs de intentos sin permiso

### **Compatibilidad:**
- [x] Clientes antiguos (created_by_user NULL) accesibles
- [x] Queries con tenant_id agregado donde faltaba
- [x] Frontend no requiere cambios (transparente)

---

## 📈 PROGRESO TOTAL

```
✅ B1: Tablas Base (100%)
✅ B2: Columnas Trazabilidad (100%)
⬜ B3: Índices Optimización (0%) - OPCIONAL
✅ B4: Permission Service (100%)
✅ B5: Endpoints Candidatos (100%)
✅ B6: Endpoints Vacantes (100%)
✅ B7: Endpoints Postulaciones (100%)
✅ B8: Endpoints Entrevistas (100%)
✅ B9: Endpoints Clientes (100%) ← ACABAMOS AQUÍ
⬜ B10: Endpoints Contratados (0%)
⬜ B11-B17: Otros endpoints (0%)
```

**Backend completado:** 8/17 módulos (47.1%)

---

## 🚀 SIGUIENTE PASO: MÓDULO B10 - Contratados

**Objetivo:** Aplicar permisos a endpoints de Contratados (último módulo de recursos principales)

**Endpoints a modificar:**
- `GET /api/hired`
- `POST /api/hired`
- `PUT /api/hired/<id>`
- `DELETE /api/hired/<id>`

**Lógica:** Similar a clientes (created_by_user directo)

**Tiempo estimado:** 45 min - 1 hora

---

## 🎯 AL COMPLETAR B10 TENDREMOS:

### **Recursos principales completados al 100%:**
- ✅ Candidatos (B5)
- ✅ Vacantes (B6)
- ✅ Postulaciones (B7)
- ✅ Entrevistas (B8)
- ✅ Clientes (B9)
- ⏳ Contratados (B10)

**¡Casi terminamos los endpoints principales!** 🎉

---

## ❓ **¿CONTINUAMOS CON B10 PARA COMPLETAR LOS RECURSOS PRINCIPALES?**

**Mi recomendación:** Sí, solo falta B10 para tener el sistema completo de reclutamiento con permisos 🚀

¿Vamos con B10? 🎯

