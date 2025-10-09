# 🔍 MÓDULO B5 - ANÁLISIS DE ENDPOINTS DE CANDIDATOS

**Fecha:** Octubre 9, 2025  
**Estado:** En progreso

---

## 📋 ENDPOINTS IDENTIFICADOS

### 1. **GET /api/candidates** (líneas 4411-4517)
**Función:** `get_candidates()`

**Situación actual:**
```python
query = """
    SELECT * FROM Afiliados a
    WHERE a.tenant_id = %s
"""
params = [tenant_id]
```

**Problema:** ❌ Todos los usuarios del tenant ven TODOS los candidatos

**Solución:**
```python
from permission_service import build_user_filter_condition

user_id = g.current_user['user_id']
condition, filter_params = build_user_filter_condition(user_id, tenant_id)

if condition:
    query += f" AND {condition}"
    params.extend(filter_params)
```

**Resultado esperado:**
- Admin: Ve todos
- Supervisor: Ve los suyos + equipo
- Reclutador: Solo los suyos

---

### 2. **POST /api/candidates** (líneas 4519-4613)
**Función:** `create_candidate()`

**Situación actual:**
```python
sql = """
    INSERT INTO Afiliados (
        nombre_completo, email, ..., tenant_id, fecha_registro
    ) VALUES (%s, %s, ..., %s, CURDATE())
"""
```

**Problema:** ❌ No registra quién creó el candidato

**Solución:**
```python
from permission_service import can_create_resource

user_id = g.current_user['user_id']

# 1. Verificar permiso
if not can_create_resource(user_id, tenant_id, 'candidate'):
    return jsonify({'error': 'No tienes permisos para crear candidatos'}), 403

# 2. Agregar created_by_user al INSERT
sql = """
    INSERT INTO Afiliados (
        nombre_completo, email, ..., tenant_id, created_by_user, fecha_registro
    ) VALUES (%s, %s, ..., %s, %s, CURDATE())
"""
cursor.execute(sql, (..., tenant_id, user_id))
```

---

### 3. **GET /api/candidates/<id>/profile** (líneas 4615-4713)
**Función:** `get_candidate_profile(candidate_id)`

**Situación actual:**
```python
cursor.execute("""
    SELECT * FROM Afiliados a
    WHERE a.id_afiliado = %s AND a.tenant_id = %s
""", (candidate_id, tenant_id))
```

**Problema:** ❌ No verifica si el usuario tiene acceso al candidato

**Solución:**
```python
from permission_service import can_access_resource

user_id = g.current_user['user_id']

# Verificar acceso
if not can_access_resource(user_id, tenant_id, 'candidate', candidate_id, 'read'):
    return jsonify({'error': 'No tienes acceso a este candidato'}), 403
```

---

### 4. **GET /api/candidates/search** (líneas 4715-4786)
**Función:** `search_candidates()`

**Situación actual:**
```python
results = _internal_search_candidates(
    term=term, 
    tags=tags, 
    # ...
)
```

**Problema:** ❌ La función interna no filtra por usuario

**Solución:**
- Modificar `_internal_search_candidates()` para aceptar `user_id`
- Aplicar `build_user_filter_condition()` dentro de la función

---

## 🔧 CAMBIOS NECESARIOS

### **Archivo:** `bACKEND/app.py`

#### Cambio 1: Importar el servicio de permisos
```python
# Línea ~65 (con otras importaciones)
from permission_service import (
    can_create_resource,
    can_access_resource,
    build_user_filter_condition,
    is_admin
)
```

#### Cambio 2: Modificar `get_candidates()`
- Agregar filtro por usuario según rol
- Líneas: 4420-4517

#### Cambio 3: Modificar `create_candidate()`
- Verificar permiso de creación
- Agregar `created_by_user` en INSERT
- Líneas: 4519-4613

#### Cambio 4: Modificar `get_candidate_profile()`
- Verificar acceso al candidato
- Líneas: 4615-4713

#### Cambio 5: Modificar `_internal_search_candidates()`
- Agregar parámetro `user_id`
- Aplicar filtro por usuario
- Líneas: 3845-4032

#### Cambio 6: Modificar `search_candidates()`
- Pasar `user_id` a la función interna
- Líneas: 4715-4786

---

## ⚠️ CONSIDERACIONES

### **Endpoints que NO requieren cambios:**
- `/api/candidates/upload` - Subida de CVs (agrega `created_by_user` automáticamente)
- `/api/candidates/check-duplicates` - Solo validación
- `/api/candidates/process-status/<job_id>` - Status de procesamiento

### **Compatibilidad hacia atrás:**
- Candidatos existentes sin `created_by_user` (NULL)
- Solución: Tratar NULL como accesible por todos (Admin)

### **Testing necesario:**
1. Usuario Admin ve todos los candidatos
2. Usuario Supervisor ve su equipo
3. Usuario Reclutador solo ve los suyos
4. Crear candidato registra `created_by_user`
5. Acceso a perfil de candidato se valida

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Importar `permission_service` en `app.py`
- [ ] Modificar `get_candidates()` con filtro por usuario
- [ ] Modificar `create_candidate()` con verificación y `created_by_user`
- [ ] Modificar `get_candidate_profile()` con verificación de acceso
- [ ] Modificar `_internal_search_candidates()` con filtro por usuario
- [ ] Modificar `search_candidates()` para pasar `user_id`
- [ ] Testing con usuarios de diferentes roles

---

**Tiempo estimado:** 1-2 horas  
**Riesgo:** Bajo (cambios localizados)

**Próximo paso:** Implementar cambios en `app.py` 🚀

