# 🔍 MÓDULO B10 - ANÁLISIS DE ENDPOINTS DE CONTRATADOS

**Fecha:** Octubre 9, 2025  
**Estado:** En progreso

---

## 📋 ENDPOINTS IDENTIFICADOS

### 1. **GET /api/hired** (líneas 6302-6340)
**Función:** `handle_hired()` (GET)

**Situación actual:**
```python
sql = """
    SELECT co.*, a.nombre_completo, v.cargo_solicitado, c.empresa
    FROM Contratados co
    JOIN Afiliados a ON co.id_afiliado = a.id_afiliado
    JOIN Vacantes v ON co.id_vacante = v.id_vacante
    JOIN Clientes c ON v.id_cliente = c.id_cliente
    ORDER BY ...
"""
cursor.execute(sql)  # Sin filtro por tenant ni usuario
```

**Problemas:**
- ❌ No filtra por `tenant_id`
- ❌ No filtra por `created_by_user`
- ❌ Todos los usuarios ven TODOS los contratados de TODOS los tenants

**Solución:**
```python
from permission_service import build_user_filter_condition

user_id = g.current_user['user_id']
tenant_id = get_current_tenant_id()

sql = """
    SELECT ...
    FROM Contratados co
    ...
    WHERE co.tenant_id = %s
"""
params = [tenant_id]

# 🔐 Filtrar por usuario según rol
condition, filter_params = build_user_filter_condition(user_id, tenant_id, 'co.created_by_user')
if condition:
    sql += f" AND ({condition} OR co.created_by_user IS NULL)"
    params.extend(filter_params)

cursor.execute(sql, tuple(params))
```

---

### 2. **POST /api/hired** (líneas 6342-6410)
**Función:** `handle_hired()` (POST)

**Situación actual:**
```python
sql_insert = """
    INSERT INTO Contratados (
        id_afiliado, id_vacante, fecha_contratacion, salario_final, tarifa_servicio, tenant_id
    ) VALUES (%s, %s, CURDATE(), %s, %s, %s)
"""
cursor.execute(sql_insert, (id_afiliado, id_vacante, ..., tenant_id))
```

**Problemas:**
- ❌ No verifica permiso de creación
- ❌ No registra `created_by_user`
- ❌ Actualiza postulación sin verificar tenant: `WHERE id_afiliado = %s AND id_vacante = %s AND tenant_id = %s` (Postulaciones NO tiene tenant_id)

**Solución:**
```python
from permission_service import can_create_resource

user_id = g.current_user['user_id']

# 1. Verificar permiso
if not can_create_resource(user_id, tenant_id, 'hired'):
    return jsonify({'error': 'No tienes permisos para registrar contrataciones'}), 403

# 2. Agregar created_by_user al INSERT
sql_insert = """
    INSERT INTO Contratados (
        id_afiliado, id_vacante, fecha_contratacion, salario_final, tarifa_servicio, tenant_id, created_by_user
    ) VALUES (%s, %s, CURDATE(), %s, %s, %s, %s)
"""
cursor.execute(sql_insert, (..., tenant_id, user_id))

# 3. Corregir UPDATE de postulación (sin tenant_id en Postulaciones)
cursor.execute("""
    UPDATE Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    SET p.estado = 'Contratado'
    WHERE p.id_afiliado = %s AND p.id_vacante = %s AND v.tenant_id = %s
""", (id_afiliado, id_vacante, tenant_id))
```

---

### 3. **POST /api/hired/<id>/payment** (líneas 6423-6498)
**Función:** `register_payment(id_contratado)`

**Situación actual:**
```python
cursor.execute("""
    SELECT c.id_afiliado, ...
    FROM Contratados c
    ...
    WHERE c.id_contratado = %s AND c.tenant_id = %s
""", (id_contratado, tenant_id))
```

**Problema:** ❌ No verifica si el usuario tiene acceso al contratado

**Solución:**
```python
from permission_service import can_access_resource

user_id = g.current_user['user_id']

# Verificar acceso con permiso de escritura
if not can_access_resource(user_id, tenant_id, 'hired', id_contratado, 'write'):
    return jsonify({'error': 'No tienes acceso a este registro de contratación'}), 403
```

---

### 4. **DELETE /api/hired/<id>** (líneas 6503-6531)
**Función:** `annul_hiring(id_contratado)`

**Situación actual:**
```python
cursor.execute("""
    SELECT id_afiliado, id_vacante 
    FROM Contratados 
    WHERE id_contratado = %s AND tenant_id = %s
""", (id_contratado, tenant_id))

# Revertir postulación
cursor.execute("""
    UPDATE Postulaciones 
    SET estado = 'Oferta' 
    WHERE id_afiliado = %s AND id_vacante = %s AND tenant_id = %s
""", (record['id_afiliado'], record['id_vacante'], tenant_id))
```

**Problemas:**
- ❌ No verifica si el usuario tiene acceso
- ❌ UPDATE de Postulaciones usa tenant_id incorrecto

**Solución:**
```python
from permission_service import can_access_resource

user_id = g.current_user['user_id']

# Verificar acceso de eliminación (requiere permiso 'full')
if not can_access_resource(user_id, tenant_id, 'hired', id_contratado, 'full'):
    return jsonify({'error': 'No tienes permisos para anular esta contratación'}), 403

# Corregir UPDATE de postulación
cursor.execute("""
    UPDATE Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    SET p.estado = 'Oferta'
    WHERE p.id_afiliado = %s AND p.id_vacante = %s AND v.tenant_id = %s
""", (record['id_afiliado'], record['id_vacante'], tenant_id))
```

---

## 🔧 CAMBIOS NECESARIOS

### **Archivo:** `bACKEND/app.py`

#### Cambio 1: Modificar GET `/api/hired`
- Agregar filtro por tenant (SIEMPRE)
- Agregar filtro por usuario según rol
- **Líneas:** 6302-6340

#### Cambio 2: Modificar POST `/api/hired`
- Verificar permiso de creación
- Agregar `created_by_user` en INSERT
- Corregir UPDATE de Postulaciones (sin tenant_id directo)
- **Líneas:** 6342-6410

#### Cambio 3: Modificar POST `/api/hired/<id>/payment`
- Verificar acceso de escritura
- **Líneas:** 6423-6498

#### Cambio 4: Modificar DELETE `/api/hired/<id>`
- Verificar acceso de eliminación (requiere 'full')
- Corregir UPDATE de Postulaciones
- **Líneas:** 6503-6531

---

## ⚠️ CONSIDERACIONES CRÍTICAS

### **Tabla Contratados tiene tenant_id DIRECTO:**

```sql
Contratados
  ├── id_contratado
  ├── id_afiliado
  ├── id_vacante
  ├── tenant_id  ← Tiene columna directa
  ├── created_by_user (nuevo en B2)
  └── ...
```

**Queries correctos:**
```sql
-- ✅ CORRECTO (tenant_id existe en Contratados)
SELECT * FROM Contratados WHERE tenant_id = %s

-- ✅ CORRECTO (con filtro de usuario)
SELECT * FROM Contratados 
WHERE tenant_id = %s 
AND (created_by_user = 8 OR created_by_user IS NULL)
```

---

### **BUG: UPDATE de Postulaciones**

**Problema actual en POST y DELETE:**
```python
# ❌ INCORRECTO (Postulaciones NO tiene tenant_id)
cursor.execute("""
    UPDATE Postulaciones 
    SET estado = 'Contratado'
    WHERE id_afiliado = %s AND id_vacante = %s AND tenant_id = %s
""")
```

**Solución:**
```python
# ✅ CORRECTO (obtener tenant de Vacantes)
cursor.execute("""
    UPDATE Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    SET p.estado = 'Contratado'
    WHERE p.id_afiliado = %s AND p.id_vacante = %s AND v.tenant_id = %s
""")
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Modificar `GET /api/hired` con filtro por usuario
- [ ] Modificar `POST /api/hired` con verificación y `created_by_user`
- [ ] Corregir UPDATE de Postulaciones en POST (sin tenant_id directo)
- [ ] Modificar `POST /api/hired/<id>/payment` con verificación de acceso
- [ ] Modificar `DELETE /api/hired/<id>` con verificación de acceso
- [ ] Corregir UPDATE de Postulaciones en DELETE (sin tenant_id directo)
- [ ] Testing con usuarios de diferentes roles

---

## 📊 MATRIZ DE PERMISOS ESPERADA

| Acción | Admin | Supervisor | Reclutador |
|--------|-------|------------|------------|
| **Ver todos los contratados** | ✅ | ❌ | ❌ |
| **Ver contratados del equipo** | ✅ | ✅ | ❌ |
| **Ver contratados propios** | ✅ | ✅ | ✅ |
| **Registrar contratación** | ✅ | ✅ | ✅ |
| **Registrar pago (propio)** | ✅ | ✅ | ✅ |
| **Registrar pago (ajeno)** | ✅ | ✅ (equipo) | ❌ |
| **Anular contratación (propio)** | ✅ | ✅ | ✅ |
| **Anular contratación (ajeno)** | ✅ | ❌ | ❌ |

---

**Tiempo estimado:** 45 min - 1 hora  
**Riesgo:** Medio (bug de tenant_id en Postulaciones)

**Próximo paso:** Implementar cambios en `app.py` 🚀

