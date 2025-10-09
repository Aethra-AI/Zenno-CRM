# 🔍 MÓDULO B9 - ANÁLISIS DE ENDPOINTS DE CLIENTES

**Fecha:** Octubre 9, 2025  
**Estado:** En progreso

---

## 📋 ENDPOINTS IDENTIFICADOS

### 1. **GET /api/clients** (líneas 6536-6563)
**Función:** `handle_clients()` (GET)

**Situación actual:**
```python
cursor.execute("""
    SELECT c.*, COUNT(DISTINCT v.id_vacante) as vacantes_count
    FROM Clientes c
    LEFT JOIN Vacantes v ON c.id_cliente = v.id_cliente AND v.tenant_id = %s
    WHERE c.tenant_id = %s
    GROUP BY c.id_cliente
""", (tenant_id, tenant_id))
```

**Problemas:**
- ❌ No filtra por `created_by_user`
- ❌ Todos los usuarios del tenant ven TODOS los clientes

**Solución:**
```python
from permission_service import build_user_filter_condition

user_id = g.current_user['user_id']

# 🔐 Filtrar por usuario según rol
condition, filter_params = build_user_filter_condition(user_id, tenant_id, 'c.created_by_user')
if condition:
    query = f"""
        SELECT c.*, COUNT(DISTINCT v.id_vacante) as vacantes_count
        FROM Clientes c
        LEFT JOIN Vacantes v ON c.id_cliente = v.id_cliente AND v.tenant_id = %s
        WHERE c.tenant_id = %s AND ({condition} OR c.created_by_user IS NULL)
        GROUP BY c.id_cliente
    """
    params = [tenant_id, tenant_id] + filter_params
else:
    # Admin: sin filtro adicional
    query = """..."""
    params = [tenant_id, tenant_id]
```

---

### 2. **POST /api/clients** (líneas 6564-6601)
**Función:** `handle_clients()` (POST)

**Situación actual:**
```python
sql = """
    INSERT INTO Clientes (
        empresa, contacto_nombre, telefono, email, sector, observaciones, tenant_id
    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
"""
cursor.execute(sql, (..., tenant_id))
```

**Problema:** ❌ No registra quién creó el cliente

**Solución:**
```python
from permission_service import can_create_resource

user_id = g.current_user['user_id']

# 1. Verificar permiso
if not can_create_resource(user_id, tenant_id, 'client'):
    return jsonify({'error': 'No tienes permisos para crear clientes'}), 403

# 2. Agregar created_by_user al INSERT
sql = """
    INSERT INTO Clientes (
        empresa, contacto_nombre, telefono, email, sector, observaciones, tenant_id, created_by_user
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""
cursor.execute(sql, (..., tenant_id, user_id))
```

---

### 3. **DELETE /api/clients/<id>** (líneas 6614-6661)
**Función:** `delete_client(client_id)`

**Situación actual:**
```python
cursor.execute("""
    SELECT id_cliente, empresa 
    FROM Clientes 
    WHERE id_cliente = %s AND tenant_id = %s
""", (client_id, tenant_id))
```

**Problema:** ❌ No verifica si el usuario tiene acceso al cliente

**Solución:**
```python
from permission_service import can_access_resource

user_id = g.current_user['user_id']

# Verificar acceso con permiso 'full'
if not can_access_resource(user_id, tenant_id, 'client', client_id, 'full'):
    return jsonify({'error': 'No tienes permisos para eliminar este cliente'}), 403
```

---

### 4. **GET /api/clients/<id>/metrics** (líneas 6663-6722)
**Función:** `get_client_metrics(client_id)`

**Situación actual:**
```python
cursor.execute("""
    SELECT id_cliente 
    FROM Clientes 
    WHERE id_cliente = %s AND tenant_id = %s
""", (client_id, tenant_id))
```

**Problema:** ❌ No verifica si el usuario tiene acceso al cliente

**Solución:**
```python
from permission_service import can_access_resource

user_id = g.current_user['user_id']

# Verificar acceso de lectura
if not can_access_resource(user_id, tenant_id, 'client', client_id, 'read'):
    return jsonify({'error': 'No tienes acceso a este cliente'}), 403
```

---

### 5. **GET /api/clients/<id>/vacancies** (líneas 8614+)
**Función:** `get_client_vacancies(client_id)`

**Problema:** ❌ Probablemente no verifica acceso al cliente

**Solución:** Similar a `/metrics`, verificar acceso antes de retornar vacantes

---

### 6. **GET /api/clients/<id>/applications** (líneas 8661+)
**Función:** `get_client_applications(client_id)`

**Problema:** ❌ Probablemente no verifica acceso al cliente

**Solución:** Similar, verificar acceso

---

### 7. **GET /api/clients/<id>/hired-candidates** (líneas 8707+)
**Función:** `get_client_hired_candidates(client_id)`

**Problema:** ❌ Probablemente no verifica acceso al cliente

**Solución:** Similar, verificar acceso

---

## 🔧 CAMBIOS NECESARIOS

### **Archivo:** `bACKEND/app.py`

#### Cambio 1: Modificar GET `/api/clients`
- Agregar filtro por usuario según rol
- Filtrar por `c.created_by_user`
- **Líneas:** 6536-6563

#### Cambio 2: Modificar POST `/api/clients`
- Verificar permiso de creación
- Agregar `created_by_user` en INSERT
- **Líneas:** 6564-6601

#### Cambio 3: Modificar DELETE `/api/clients/<id>`
- Verificar acceso con `can_access_resource()`
- Solo Admin o creador pueden eliminar
- **Líneas:** 6614-6661

#### Cambio 4: Modificar GET `/api/clients/<id>/metrics`
- Verificar acceso de lectura
- **Líneas:** 6663-6722

#### Cambio 5: Modificar GET `/api/clients/<id>/vacancies`
- Verificar acceso de lectura
- **Líneas:** 8614+

#### Cambio 6: Modificar GET `/api/clients/<id>/applications`
- Verificar acceso de lectura
- **Líneas:** 8661+

#### Cambio 7: Modificar GET `/api/clients/<id>/hired-candidates`
- Verificar acceso de lectura
- **Líneas:** 8707+

---

## ⚠️ CONSIDERACIONES

### **Clientes tienen created_by_user DIRECTO:**

A diferencia de postulaciones y entrevistas, los clientes tienen su propia columna `created_by_user`:

```sql
Clientes
  ├── id_cliente
  ├── empresa
  ├── tenant_id
  ├── created_by_user  ← Columna directa (agregada en B2)
  └── ...
```

**Queries correctos:**
```sql
-- ✅ CORRECTO (filtro directo)
SELECT * FROM Clientes 
WHERE tenant_id = %s AND created_by_user = %s

-- ✅ CORRECTO (con condición dinámica)
SELECT * FROM Clientes 
WHERE tenant_id = %s 
AND (created_by_user IN (5, 8, 12) OR created_by_user IS NULL)
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Modificar `GET /api/clients` con filtro por usuario
- [ ] Modificar `POST /api/clients` con verificación y `created_by_user`
- [ ] Modificar `DELETE /api/clients/<id>` con verificación de acceso
- [ ] Modificar `GET /api/clients/<id>/metrics` con verificación de acceso
- [ ] Modificar `GET /api/clients/<id>/vacancies` con verificación de acceso
- [ ] Modificar `GET /api/clients/<id>/applications` con verificación de acceso
- [ ] Modificar `GET /api/clients/<id>/hired-candidates` con verificación de acceso
- [ ] Testing con usuarios de diferentes roles

---

## 📊 MATRIZ DE PERMISOS ESPERADA

| Acción | Admin | Supervisor | Reclutador |
|--------|-------|------------|------------|
| **Ver todos los clientes** | ✅ | ❌ | ❌ |
| **Ver clientes del equipo** | ✅ | ✅ | ❌ |
| **Ver clientes propios** | ✅ | ✅ | ✅ |
| **Crear cliente** | ✅ | ✅ | ✅ |
| **Ver métricas de cliente propio** | ✅ | ✅ | ✅ |
| **Ver métricas de cliente del equipo** | ✅ | ✅ | ❌ |
| **Eliminar cliente propio** | ✅ | ✅ | ✅ |
| **Eliminar cliente ajeno** | ✅ | ❌ | ❌ |

---

**Tiempo estimado:** 1-1.5 horas  
**Riesgo:** Bajo (patrón directo como candidatos y vacantes)

**Próximo paso:** Implementar cambios en `app.py` 🚀

