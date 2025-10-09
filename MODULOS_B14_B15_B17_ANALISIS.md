# 🔍 MÓDULOS B14, B15, B17 - ANÁLISIS COMPLETO

**Fecha:** Octubre 9, 2025  
**Estado:** Análisis completo

---

## 📋 RESUMEN EJECUTIVO

Estos 3 módulos son **SIMPLES** comparados con los anteriores:
- **B14 (Tags):** Ya tiene `tenant_id`, solo necesita validar acceso a candidatos
- **B15 (Templates):** Ya tiene `tenant_id`, con 1 BUG en UPDATE
- **B17 (Calendar):** Ya tiene `tenant_id`, necesita filtros por usuario

**Tiempo estimado:** 1-1.5 horas para los 3 módulos

---

## 🔧 MÓDULO B14: TAGS

### **Endpoints identificados:**

#### 1. GET `/api/tags` (línea 3297)
**Estado:** ✅ **YA ESTÁ BIEN**
```python
cursor.execute("SELECT * FROM Tags WHERE tenant_id = %s ...", (tenant_id,))
```
- ✅ Ya filtra por `tenant_id`
- ✅ Solo lista tags del tenant
- ❌ **No necesita** filtro por usuario (todos ven los tags del tenant)

---

#### 2. POST `/api/tags` (línea 3297)
**Estado:** ✅ **YA ESTÁ BIEN**
```python
cursor.execute("INSERT INTO Tags (nombre_tag, tenant_id) VALUES (%s, %s)", (nombre_tag, tenant_id))
```
- ✅ Ya incluye `tenant_id`
- ✅ Tags son a nivel de tenant
- ❌ **No necesita** filtro por usuario (todos pueden crear tags)

---

#### 3. GET `/api/candidate/<id>/tags` (línea 3329)
**Estado:** ⚠️ **NECESITA MEJORA**

**Situación actual:**
```python
# Verifica que candidato pertenece al tenant
cursor.execute("SELECT id_afiliado FROM Afiliados WHERE id_afiliado = %s AND tenant_id = %s", (id_afiliado, tenant_id))
if not cursor.fetchone():
    return jsonify({"error": "Candidato no encontrado"}), 404
```

**Problema:** ❌ NO verifica si el usuario tiene acceso al candidato

**Solución:**
```python
# 🔐 MÓDULO B14: Verificar acceso al candidato
if not can_access_resource(user_id, tenant_id, 'candidate', id_afiliado, 'read'):
    return jsonify({'error': 'No tienes acceso a este candidato'}), 403
```

---

#### 4. POST `/api/candidate/<id>/tags` (línea 3329)
**Estado:** ⚠️ **NECESITA MEJORA**

**Problema:** ❌ NO verifica si el usuario tiene acceso al candidato

**Solución:**
```python
# 🔐 MÓDULO B14: Verificar acceso al candidato
if not can_access_resource(user_id, tenant_id, 'candidate', id_afiliado, 'write'):
    return jsonify({'error': 'No tienes acceso a este candidato'}), 403
```

---

#### 5. DELETE `/api/candidate/<id>/tags` (línea 3329)
**Estado:** ⚠️ **NECESITA MEJORA**

**Problema:** ❌ NO verifica si el usuario tiene acceso al candidato

**Solución:**
```python
# 🔐 MÓDULO B14: Verificar acceso al candidato
if not can_access_resource(user_id, tenant_id, 'candidate', id_afiliado, 'write'):
    return jsonify({'error': 'No tienes acceso a este candidato'}), 403
```

---

## 🔧 MÓDULO B15: TEMPLATES

### **Endpoints identificados:**

#### 1. GET `/api/templates` (línea 3379)
**Estado:** ✅ **YA ESTÁ BIEN**
```python
cursor.execute("SELECT ... FROM Email_Templates WHERE tenant_id = %s ...", (tenant_id,))
```
- ✅ Ya filtra por `tenant_id`
- ✅ Templates son a nivel de tenant
- ❌ **No necesita** filtro por usuario (todos ven los templates del tenant)

---

#### 2. POST `/api/templates` (línea 3379)
**Estado:** ✅ **YA ESTÁ BIEN**
```python
cursor.execute("INSERT INTO Email_Templates (..., tenant_id) VALUES (..., %s)", (..., tenant_id))
```
- ✅ Ya incluye `tenant_id`
- ❌ **No necesita** filtro por usuario (todos pueden crear templates)

---

#### 3. GET `/api/templates/<id>` (línea 3401)
**Estado:** ✅ **YA ESTÁ BIEN**
```python
cursor.execute("SELECT * FROM Email_Templates WHERE id_template = %s AND tenant_id = %s", (id_template, tenant_id))
```
- ✅ Ya filtra por `tenant_id`

---

#### 4. PUT `/api/templates/<id>` (línea 3401) 🚨
**Estado:** ❌ **BUG CRÍTICO**

**Problema:**
```python
sql = "UPDATE Email_Templates SET ... WHERE id_template=%s AND id_cliente=%s"
cursor.execute(sql, (..., id_template, tenant_id))
                                       ^^^^^^^^ 
# ❌ Usa tenant_id pero la columna se llama "id_cliente" (INCORRECTO)
```

**Solución:**
```python
sql = "UPDATE Email_Templates SET ... WHERE id_template=%s AND tenant_id=%s"
cursor.execute(sql, (..., id_template, tenant_id))
```

---

#### 5. DELETE `/api/templates/<id>` (línea 3401)
**Estado:** ✅ **YA ESTÁ BIEN**
```python
cursor.execute("DELETE FROM Email_Templates WHERE id_template = %s AND tenant_id = %s", (id_template, tenant_id))
```
- ✅ Ya filtra por `tenant_id`

---

## 🔧 MÓDULO B17: CALENDAR

### **Endpoints identificados:**

#### 1. GET `/api/calendar/reminders` (línea 8612)
**Estado:** ⚠️ **NECESITA MEJORA (OPCIONAL)**

**Situación actual:**
```python
cursor.execute("""
    SELECT r.*, u.username as created_by_name
    FROM calendar_reminders r
    WHERE r.tenant_id = %s 
    ORDER BY r.date, r.time
""", (tenant_id, year, month))
```

- ✅ Ya filtra por `tenant_id`
- ❌ NO filtra por usuario (todos ven TODOS los recordatorios del tenant)

**Solución (OPCIONAL):**
- Opción 1: Dejar como está (recordatorios visibles para todos)
- Opción 2: Filtrar por `created_by` o `assigned_to` para que solo vean los suyos

**Recomendación:** Dejar como está (los recordatorios son colaborativos)

---

#### 2. POST `/api/calendar/reminders` (línea 8612)
**Estado:** ✅ **YA ESTÁ BIEN**
```python
cursor.execute("""
    INSERT INTO calendar_reminders (..., tenant_id, created_by) VALUES (..., %s, %s)
""", (..., tenant_id, user_id))
```
- ✅ Ya incluye `tenant_id`
- ✅ Ya incluye `created_by`

---

#### 3. GET `/api/calendar/interviews` (línea 8684)
**Estado:** ⚠️ **NECESITA MEJORA**

**Situación actual:**
```python
cursor.execute("""
    SELECT i.*, a.nombre_completo, v.cargo_solicitado
    FROM interviews i
    LEFT JOIN Afiliados a ON i.candidate_id = a.id_afiliado
    LEFT JOIN Vacantes v ON i.vacancy_id = v.id_vacante
    WHERE i.tenant_id = %s 
    ORDER BY i.interview_date
""", (tenant_id, year, month))
```

- ✅ Ya filtra por `tenant_id`
- ❌ NO filtra por usuario (todos ven TODAS las entrevistas)

**Solución:**
```python
# 🔐 MÓDULO B17: Filtrar entrevistas por usuario
vacancy_condition, vacancy_params = build_user_filter_condition(user_id, tenant_id, 'v.created_by_user')

sql = """
    SELECT ...
    FROM interviews i
    ...
    WHERE i.tenant_id = %s AND v.tenant_id = %s
"""
params = [tenant_id, tenant_id, year, month]
if vacancy_condition:
    sql += f" AND ({vacancy_condition} OR v.created_by_user IS NULL)"
    params[1:1] = vacancy_params  # Insertar params después de tenant_id
```

---

#### 4. GET `/api/calendar/activities` (línea 8741)
**Estado:** ❌ **BUG CRÍTICO**

**Problema:**
```python
# Postulaciones NO filtran por tenant
cursor.execute("""
    SELECT ... FROM Postulaciones p
    WHERE YEAR(p.fecha_aplicacion) = %s 
    AND MONTH(p.fecha_aplicacion) = %s
    ...
""", (year, month, tenant_id, year, month))
```

- ❌ Postulaciones NO filtran por `tenant_id`
- ❌ NO filtran por usuario

**Solución:**
```python
vacancy_condition, vacancy_params = build_user_filter_condition(user_id, tenant_id, 'v.created_by_user')

sql = """
    SELECT ... FROM Postulaciones p
    LEFT JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE v.tenant_id = %s
    AND YEAR(p.fecha_aplicacion) = %s 
    AND MONTH(p.fecha_aplicacion) = %s
"""
if vacancy_condition:
    sql += f" AND ({vacancy_condition} OR v.created_by_user IS NULL)"
```

---

#### 5. PUT/DELETE `/api/calendar/reminders/<id>` (línea 8810)
**Estado:** ✅ **YA ESTÁ BIEN**

```python
# Ya verifica que el recordatorio existe y pertenece al tenant
cursor.execute("SELECT * FROM calendar_reminders WHERE id = %s AND tenant_id = %s", (reminder_id, tenant_id))

# Ya verifica permisos (solo el creador puede modificar/eliminar)
if reminder['created_by'] != user_id and g.current_user['role'] not in ['admin', 'supervisor']:
    return jsonify({'error': 'No tienes permisos'}), 403
```

- ✅ Ya filtra por `tenant_id`
- ✅ Ya verifica permisos por `created_by`
- ✅ NO necesita cambios

---

## 🎯 RESUMEN DE CAMBIOS NECESARIOS

### **B14: Tags (3 cambios)**
1. ✅ GET `/api/tags` - Sin cambios
2. ✅ POST `/api/tags` - Sin cambios
3. ⚠️ GET/POST/DELETE `/api/candidate/<id>/tags` - Agregar `can_access_resource`

### **B15: Templates (1 cambio)**
1. ✅ GET `/api/templates` - Sin cambios
2. ✅ POST `/api/templates` - Sin cambios
3. ✅ GET `/api/templates/<id>` - Sin cambios
4. 🚨 PUT `/api/templates/<id>` - Corregir `id_cliente` → `tenant_id`
5. ✅ DELETE `/api/templates/<id>` - Sin cambios

### **B17: Calendar (2 cambios)**
1. ✅ GET `/api/calendar/reminders` - Sin cambios (opcional)
2. ✅ POST `/api/calendar/reminders` - Sin cambios
3. ⚠️ GET `/api/calendar/interviews` - Agregar filtro por usuario
4. 🚨 GET `/api/calendar/activities` - Agregar filtro por tenant y usuario
5. ✅ PUT/DELETE `/api/calendar/reminders/<id>` - Sin cambios

---

## 🐛 BUGS CRÍTICOS IDENTIFICADOS

### **Bug 1: UPDATE de Templates usa columna incorrecta** 🚨
**Módulo:** B15  
**Línea:** 3417  
**Gravedad:** ALTA

**Antes:**
```python
sql = "UPDATE Email_Templates SET ... WHERE id_template=%s AND id_cliente=%s"
                                                                 ^^^^^^^^^^
# ❌ Columna "id_cliente" no existe en Email_Templates
```

**Después:**
```python
sql = "UPDATE Email_Templates SET ... WHERE id_template=%s AND tenant_id=%s"
                                                                ^^^^^^^^^^
# ✅ Columna correcta
```

---

### **Bug 2: Calendar Activities sin filtro de tenant en Postulaciones** 🚨
**Módulo:** B17  
**Línea:** 8754  
**Gravedad:** CRÍTICA

**Antes:**
```python
SELECT ... FROM Postulaciones p
WHERE YEAR(p.fecha_aplicacion) = %s 
# ❌ Sin filtro por tenant
```

**Después:**
```python
SELECT ... FROM Postulaciones p
JOIN Vacantes v ON p.id_vacante = v.id_vacante
WHERE v.tenant_id = %s AND YEAR(p.fecha_aplicacion) = %s
# ✅ Con filtro por tenant
```

---

## 📊 COMPLEJIDAD

| Módulo | Endpoints | Cambios | Complejidad | Tiempo |
|--------|-----------|---------|-------------|--------|
| **B14** | 2 grupos (5 rutas) | 3 pequeños | Baja | 20 min |
| **B15** | 3 endpoints | 1 crítico | Baja | 15 min |
| **B17** | 5 endpoints | 2 medianos | Media | 30 min |

**Tiempo total:** 1-1.5 horas

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### **B14: Tags**
- [ ] Agregar `can_access_resource` en GET `/api/candidate/<id>/tags`
- [ ] Agregar `can_access_resource` en POST `/api/candidate/<id>/tags`
- [ ] Agregar `can_access_resource` en DELETE `/api/candidate/<id>/tags`

### **B15: Templates**
- [ ] Corregir columna en PUT `/api/templates/<id>` (id_cliente → tenant_id)

### **B17: Calendar**
- [ ] Agregar filtro por usuario en GET `/api/calendar/interviews`
- [ ] Agregar filtro por tenant y usuario en GET `/api/calendar/activities`

---

**Tiempo estimado:** 1-1.5 horas  
**Riesgo:** Bajo

**Próximo paso:** Implementar cambios en `app.py` 🚀

