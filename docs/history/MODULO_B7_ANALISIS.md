# 🔍 MÓDULO B7 - ANÁLISIS DE ENDPOINTS DE POSTULACIONES

**Fecha:** Octubre 9, 2025  
**Estado:** En progreso

---

## 📋 ENDPOINTS IDENTIFICADOS

### 1. **GET /api/applications** (líneas 5646-5705)
**Función:** `handle_applications()` (GET)

**Situación actual:**
```python
user_role = getattr(g, 'current_user', {}).get('rol', '')

if user_role != 'Administrador':  # ❌ Compara string directamente
    conditions.append("v.tenant_id = %s")
    params.append(tenant_id)
```

**Problemas:**
- ❌ Compara rol como string en vez de usar `permission_service`
- ❌ Admin ve TODAS las postulaciones (sin filtro)
- ❌ No filtra por `created_by_user`
- ❌ Todos los usuarios del tenant ven TODAS las postulaciones

**Solución:**
```python
from permission_service import build_user_filter_condition

user_id = g.current_user['user_id']

# Siempre filtrar por tenant
conditions.append("v.tenant_id = %s")
params.append(tenant_id)

# 🔐 Filtrar por usuario según rol
condition, filter_params = build_user_filter_condition(user_id, tenant_id, 'p.created_by_user')
if condition:
    conditions.append(f"({condition} OR p.created_by_user IS NULL)")
    params.extend(filter_params)
```

---

### 2. **POST /api/applications** (líneas 5707-5816)
**Función:** `handle_applications()` (POST)

**Situación actual:**
```python
sql = """
    INSERT INTO Postulaciones (
        id_afiliado, id_vacante, fecha_aplicacion, estado, comentarios
    ) VALUES (%s, %s, NOW(), 'Recibida', %s)
"""
```

**Problema:** ❌ No registra quién creó la postulación

**Solución:**
```python
from permission_service import can_create_resource

user_id = g.current_user['user_id']

# 1. Verificar permiso
if not can_create_resource(user_id, tenant_id, 'application'):
    return jsonify({'error': 'No tienes permisos para crear postulaciones'}), 403

# 2. Agregar created_by_user al INSERT
sql = """
    INSERT INTO Postulaciones (
        id_afiliado, id_vacante, fecha_aplicacion, estado, comentarios, created_by_user
    ) VALUES (%s, %s, NOW(), 'Recibida', %s, %s)
"""
cursor.execute(sql, (data['id_afiliado'], data['id_vacante'], data.get('comentarios', ''), user_id))
```

---

### 3. **PUT /api/applications/<id>/status** (líneas 3568-3650)
**Función:** `update_application_status(id_postulacion)`

**Situación actual:**
```python
cursor.execute("""
    SELECT p.id_postulacion, p.id_afiliado, p.id_vacante, v.id_cliente
    FROM Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.id_postulacion = %s AND v.tenant_id = %s
""", (id_postulacion, tenant_id))
```

**Problema:** ❌ No verifica si el usuario tiene acceso a la postulación

**Solución:**
```python
from permission_service import can_access_resource

user_id = g.current_user['user_id']

# Verificar acceso con permiso de escritura
# Nota: Verificamos acceso indirectamente a través de la vacante
cursor.execute("""
    SELECT p.id_postulacion, p.id_vacante, v.cargo_solicitado
    FROM Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.id_postulacion = %s AND v.tenant_id = %s
""", (id_postulacion, tenant_id))

postulacion = cursor.fetchone()
if not postulacion:
    return jsonify({"error": "Postulación no encontrada"}), 404

# Verificar acceso a la vacante relacionada
vacancy_id = postulacion['id_vacante']
if not can_access_resource(user_id, tenant_id, 'vacancy', vacancy_id, 'write'):
    return jsonify({'error': 'No tienes acceso a esta postulación'}), 403
```

---

### 4. **DELETE /api/applications/<id>** (líneas 5824-5851)
**Función:** `delete_application(id_postulacion)`

**Situación actual:**
```python
cursor.execute("""
    SELECT id_postulacion 
    FROM Postulaciones 
    WHERE id_postulacion = %s AND tenant_id = %s
""", (id_postulacion, tenant_id))
```

**Problema:** 
- ❌ No verifica si el usuario tiene acceso
- ❌ Usa columna `tenant_id` directamente en Postulaciones (puede no existir)

**Solución:**
```python
from permission_service import can_access_resource

user_id = g.current_user['user_id']

# Verificar que la postulación existe y obtener su vacante
cursor.execute("""
    SELECT p.id_postulacion, p.id_vacante, v.tenant_id
    FROM Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.id_postulacion = %s AND v.tenant_id = %s
""", (id_postulacion, tenant_id))

postulacion = cursor.fetchone()
if not postulacion:
    return jsonify({"success": False, "error": "Postulación no encontrada."}), 404

# Verificar acceso (requiere permiso 'full')
vacancy_id = postulacion['id_vacante']
if not can_access_resource(user_id, tenant_id, 'vacancy', vacancy_id, 'full'):
    return jsonify({'error': 'No tienes permisos para eliminar esta postulación'}), 403
```

---

### 5. **PUT /api/applications/<id>/comments** (líneas 5856-5883)
**Función:** `update_application_comments(id_postulacion)`

**Situación actual:**
```python
sql = "UPDATE Postulaciones SET comentarios = %s WHERE id_postulacion = %s"
cursor.execute(sql, (nuevos_comentarios, id_postulacion))
```

**Problema:** ❌ No verifica tenant_id ni acceso del usuario

**Solución:**
```python
from permission_service import can_access_resource

user_id = g.current_user['user_id']
tenant_id = get_current_tenant_id()

# Verificar que la postulación existe y obtener su vacante
cursor.execute("""
    SELECT p.id_postulacion, p.id_vacante, v.tenant_id
    FROM Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.id_postulacion = %s AND v.tenant_id = %s
""", (id_postulacion, tenant_id))

postulacion = cursor.fetchone()
if not postulacion:
    return jsonify({"success": False, "error": "Postulación no encontrada."}), 404

# Verificar acceso de escritura
vacancy_id = postulacion['id_vacante']
if not can_access_resource(user_id, tenant_id, 'vacancy', vacancy_id, 'write'):
    return jsonify({'error': 'No tienes permisos para editar esta postulación'}), 403
```

---

## 🔧 CAMBIOS NECESARIOS

### **Archivo:** `bACKEND/app.py`

#### Cambio 1: Modificar GET `/api/applications`
- Reemplazar lógica de rol por `build_user_filter_condition()`
- Siempre filtrar por tenant (incluso Admin)
- Agregar filtro por usuario según rol
- **Líneas:** 5646-5705

#### Cambio 2: Modificar POST `/api/applications`
- Verificar permiso de creación
- Agregar `created_by_user` en INSERT
- **Líneas:** 5707-5816

#### Cambio 3: Modificar PUT `/api/applications/<id>/status`
- Verificar acceso a través de la vacante relacionada
- Solo permitir si tiene acceso a la vacante
- **Líneas:** 3568-3650

#### Cambio 4: Modificar DELETE `/api/applications/<id>`
- Verificar acceso a través de la vacante relacionada
- Requiere permiso 'full' en la vacante
- Corregir query para obtener tenant_id de Vacantes
- **Líneas:** 5824-5851

#### Cambio 5: Modificar PUT `/api/applications/<id>/comments`
- Verificar acceso a través de la vacante relacionada
- Agregar tenant_id a la verificación
- **Líneas:** 5856-5883

---

## ⚠️ CONSIDERACIONES

### **Esquema de Postulaciones:**
**IMPORTANTE:** La tabla `Postulaciones` NO tiene columna `tenant_id` directamente.
El tenant se obtiene a través de `Vacantes`:

```sql
Postulaciones
  ├── id_postulacion
  ├── id_afiliado
  ├── id_vacante  ← JOIN con Vacantes
  ├── created_by_user (nuevo)
  └── ...

Vacantes
  ├── id_vacante
  ├── tenant_id  ← Aquí está el tenant
  └── ...
```

**Queries correctos:**
```sql
-- ❌ INCORRECTO (tenant_id no existe en Postulaciones)
SELECT * FROM Postulaciones WHERE tenant_id = %s

-- ✅ CORRECTO (obtener tenant de Vacantes)
SELECT p.* 
FROM Postulaciones p
JOIN Vacantes v ON p.id_vacante = v.id_vacante
WHERE v.tenant_id = %s
```

### **Permisos indirectos:**
Las postulaciones no tienen permisos propios, se heredan de la vacante:
- Puedes editar una postulación SI tienes acceso a su vacante
- Puedes eliminar una postulación SI tienes acceso completo a su vacante

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Modificar `GET /api/applications` con filtro por usuario
- [ ] Modificar `POST /api/applications` con verificación y `created_by_user`
- [ ] Modificar `PUT /api/applications/<id>/status` con verificación de acceso
- [ ] Modificar `DELETE /api/applications/<id>` con verificación de acceso
- [ ] Modificar `PUT /api/applications/<id>/comments` con verificación de acceso
- [ ] Testing con usuarios de diferentes roles

---

## 📊 MATRIZ DE PERMISOS ESPERADA

| Acción | Admin | Supervisor | Reclutador |
|--------|-------|------------|------------|
| **Ver todas las postulaciones** | ✅ | ❌ | ❌ |
| **Ver postulaciones de vacantes del equipo** | ✅ | ✅ | ❌ |
| **Ver postulaciones de vacantes propias** | ✅ | ✅ | ✅ |
| **Crear postulación** | ✅ | ✅ | ✅ |
| **Cambiar estado (vacante propia)** | ✅ | ✅ | ✅ |
| **Cambiar estado (vacante del equipo)** | ✅ | ✅ | ❌ |
| **Eliminar postulación (vacante propia)** | ✅ | ✅ | ✅ |
| **Eliminar postulación (vacante ajena)** | ✅ | ❌ | ❌ |

**Nota:** Los permisos se verifican a través de la vacante, NO directamente en la postulación.

---

**Tiempo estimado:** 1.5-2 horas  
**Riesgo:** Medio (lógica indirecta a través de vacantes)

**Próximo paso:** Implementar cambios en `app.py` 🚀

