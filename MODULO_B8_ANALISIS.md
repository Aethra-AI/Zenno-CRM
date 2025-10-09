# 🔍 MÓDULO B8 - ANÁLISIS DE ENDPOINTS DE ENTREVISTAS

**Fecha:** Octubre 9, 2025  
**Estado:** En progreso

---

## 📋 ENDPOINTS IDENTIFICADOS

### 1. **GET /api/interviews** (líneas 5960-5998)
**Función:** `handle_interviews()` (GET)

**Situación actual:**
```python
sql = """
    SELECT e.*, a.nombre_completo, v.cargo_solicitado
    FROM Entrevistas e
    JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    ...
"""
# No hay filtro por tenant ni por usuario
```

**Problemas:**
- ❌ No filtra por tenant_id
- ❌ No filtra por `created_by_user`
- ❌ Todos los usuarios ven TODAS las entrevistas

**Solución:**
```python
from permission_service import build_user_filter_condition

user_id = g.current_user['user_id']

# Siempre filtrar por tenant
conditions.append("v.tenant_id = %s")
params.append(tenant_id)

# 🔐 Filtrar por usuario según rol (a través de la vacante)
condition, filter_params = build_user_filter_condition(user_id, tenant_id, 'v.created_by_user')
if condition:
    conditions.append(f"({condition} OR v.created_by_user IS NULL)")
    params.extend(filter_params)
```

---

### 2. **POST /api/interviews** (líneas 6000-6112)
**Función:** `handle_interviews()` (POST)

**Situación actual:**
```python
# Verificar que la postulación pertenece al tenant
cursor.execute("""
    SELECT id_postulacion 
    FROM Postulaciones 
    WHERE id_postulacion = %s AND tenant_id = %s
""", (id_postulacion, tenant_id))

sql_insert = """
    INSERT INTO Entrevistas (
        id_postulacion, fecha_hora, entrevistador, resultado, observaciones, id_cliente
    ) VALUES (%s, %s, %s, 'Programada', %s, %s)
"""
```

**Problemas:**
- ❌ No verifica permiso de creación
- ❌ No registra `created_by_user`
- ❌ Query incorrecta: `Postulaciones.tenant_id` no existe

**Solución:**
```python
from permission_service import can_create_resource

user_id = g.current_user['user_id']

# 1. Verificar permiso
if not can_create_resource(user_id, tenant_id, 'interview'):
    return jsonify({'error': 'No tienes permisos para agendar entrevistas'}), 403

# 2. Verificar postulación correctamente (a través de Vacantes)
cursor.execute("""
    SELECT p.id_postulacion, v.id_vacante, v.tenant_id
    FROM Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.id_postulacion = %s AND v.tenant_id = %s
""", (id_postulacion, tenant_id))

# 3. Agregar created_by_user al INSERT
sql_insert = """
    INSERT INTO Entrevistas (
        id_postulacion, fecha_hora, entrevistador, resultado, observaciones, id_cliente, created_by_user
    ) VALUES (%s, %s, %s, 'Programada', %s, %s, %s)
"""
cursor.execute(sql_insert, (..., tenant_id, user_id))
```

---

### 3. **DELETE /api/interviews/<id>** (líneas 6118-6164)
**Función:** `delete_interview(id_entrevista)`

**Situación actual:**
```python
cursor.execute("""
    SELECT e.id_entrevista, ...
    FROM Entrevistas e
    JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE e.id_entrevista = %s AND e.id_cliente = %s
""", (id_entrevista, tenant_id))
```

**Problema:** ❌ No verifica si el usuario tiene acceso

**Solución:**
```python
from permission_service import can_access_resource

user_id = g.current_user['user_id']

# Obtener información de la entrevista y su vacante
cursor.execute("""
    SELECT e.id_entrevista, p.id_vacante, v.tenant_id
    FROM Entrevistas e
    JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE e.id_entrevista = %s AND v.tenant_id = %s
""", (id_entrevista, tenant_id))

entrevista = cursor.fetchone()
if not entrevista:
    return jsonify({"error": "Entrevista no encontrada"}), 404

# Verificar acceso de eliminación a través de la vacante
vacancy_id = entrevista['id_vacante']
if not can_access_resource(user_id, tenant_id, 'vacancy', vacancy_id, 'full'):
    return jsonify({'error': 'No tienes permisos para eliminar esta entrevista'}), 403
```

---

### 4. **GET /api/interviews/stats** (líneas 6166+)
**Función:** `get_interview_stats()`

**Situación actual:**
```python
sql = """
    SELECT e.*, ...
    FROM Entrevistas e
    ...
    WHERE v.tenant_id = %s
"""
```

**Problema:** ❌ No filtra por usuario

**Solución:**
```python
# Agregar filtro por usuario al WHERE
condition, filter_params = build_user_filter_condition(user_id, tenant_id, 'v.created_by_user')
if condition:
    sql += f" AND ({condition} OR v.created_by_user IS NULL)"
    params.extend(filter_params)
```

---

## 🔧 CAMBIOS NECESARIOS

### **Archivo:** `bACKEND/app.py`

#### Cambio 1: Modificar GET `/api/interviews`
- Agregar filtro por tenant (SIEMPRE)
- Agregar filtro por usuario según rol (a través de vacante)
- **Líneas:** 5960-5998

#### Cambio 2: Modificar POST `/api/interviews`
- Verificar permiso de creación
- Corregir query de validación de postulación (usar Vacantes)
- Agregar `created_by_user` en INSERT
- **Líneas:** 6000-6112

#### Cambio 3: Modificar DELETE `/api/interviews/<id>`
- Verificar acceso a través de la vacante relacionada
- Requiere permiso 'full' en la vacante
- **Líneas:** 6118-6164

#### Cambio 4: Modificar GET `/api/interviews/stats`
- Agregar filtro por usuario según rol
- **Líneas:** 6166+

---

## ⚠️ CONSIDERACIONES

### **Esquema de Entrevistas:**

**Estructura de relaciones:**
```
Vacantes (tiene created_by_user)
  ├── Postulaciones
  │     └── Entrevistas
```

**Lógica de permisos:**
- Las entrevistas NO tienen permisos propios
- Heredan permisos de la vacante (a través de la postulación)
- Si puedes gestionar la vacante → puedes gestionar sus entrevistas
- Si puedes ver la vacante → puedes ver sus entrevistas

**Queries correctos:**
```sql
-- ❌ INCORRECTO (Postulaciones NO tiene tenant_id)
SELECT p.* FROM Postulaciones p WHERE tenant_id = %s

-- ❌ INCORRECTO (Entrevistas usa id_cliente como tenant)
SELECT e.* FROM Entrevistas e WHERE e.id_cliente = %s

-- ✅ CORRECTO (obtener tenant de Vacantes)
SELECT e.* 
FROM Entrevistas e
JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
JOIN Vacantes v ON p.id_vacante = v.id_vacante
WHERE v.tenant_id = %s
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Modificar `GET /api/interviews` con filtro por usuario
- [ ] Modificar `POST /api/interviews` con verificación y `created_by_user`
- [ ] Modificar `DELETE /api/interviews/<id>` con verificación de acceso
- [ ] Modificar `GET /api/interviews/stats` con filtro por usuario (OPCIONAL)
- [ ] Testing con usuarios de diferentes roles

---

## 📊 MATRIZ DE PERMISOS ESPERADA

| Acción | Admin | Supervisor | Reclutador |
|--------|-------|------------|------------|
| **Ver todas las entrevistas** | ✅ | ❌ | ❌ |
| **Ver entrevistas de vacantes del equipo** | ✅ | ✅ | ❌ |
| **Ver entrevistas de vacantes propias** | ✅ | ✅ | ✅ |
| **Agendar entrevista** | ✅ | ✅ | ✅ |
| **Eliminar entrevista (vacante propia)** | ✅ | ✅ | ✅ |
| **Eliminar entrevista (vacante ajena)** | ✅ | ❌ | ❌ |

**Nota:** Los permisos se verifican a través de la vacante, igual que en postulaciones (B7).

---

**Tiempo estimado:** 1-1.5 horas  
**Riesgo:** Bajo (mismo patrón que B7)

**Próximo paso:** Implementar cambios en `app.py` 🚀

