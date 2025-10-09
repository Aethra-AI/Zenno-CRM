# 🔍 MÓDULO B6 - ANÁLISIS DE ENDPOINTS DE VACANTES

**Fecha:** Octubre 9, 2025  
**Estado:** En progreso

---

## 📋 ENDPOINTS IDENTIFICADOS

### 1. **GET /api/vacancies** (líneas 5373-5438)
**Función:** `handle_vacancies()` (GET)

**Situación actual:**
```python
user_role = getattr(g, 'current_user', {}).get('rol', '')
if user_role == 'Administrador':  # ❌ Compara string directamente
    # Ve todas las vacantes
else:
    # WHERE V.id_cliente = %s  ❌ Filtro incorrecto (por tenant, no por usuario)
    params = [tenant_id]
```

**Problemas:**
- ❌ Compara rol como string en vez de usar `permission_service`
- ❌ Filtro incorrecto: usa `id_cliente` en vez de `tenant_id`
- ❌ No filtra por `created_by_user`
- ❌ Todos los usuarios del tenant ven TODAS las vacantes

**Solución:**
```python
from permission_service import build_user_filter_condition

user_id = g.current_user['user_id']
base_query = """
    SELECT V.*, C.empresa, COUNT(P.id_postulacion) as aplicaciones 
    FROM Vacantes V 
    JOIN Clientes C ON V.id_cliente = C.id_cliente
    LEFT JOIN Postulaciones P ON V.id_vacante = P.id_vacante
    WHERE V.tenant_id = %s
    GROUP BY V.id_vacante, C.empresa
"""
params = [tenant_id]

# 🔐 Filtrar por usuario según rol
condition, filter_params = build_user_filter_condition(user_id, tenant_id, 'V.created_by_user')
if condition:
    # Insertar condición ANTES del GROUP BY
    base_query = base_query.replace('GROUP BY', f'AND ({condition} OR V.created_by_user IS NULL) GROUP BY')
    params.extend(filter_params)
```

---

### 2. **POST /api/vacancies** (líneas 5439-5524)
**Función:** `handle_vacancies()` (POST)

**Situación actual:**
```python
sql = """
    INSERT INTO Vacantes (
        id_cliente, cargo_solicitado, descripcion, ciudad, requisitos, 
        salario_min, salario_max, salario, fecha_apertura, estado, tenant_id
    ) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURDATE(), 'Abierta', %s)
"""
```

**Problema:** ❌ No registra quién creó la vacante

**Solución:**
```python
from permission_service import can_create_resource

user_id = g.current_user['user_id']

# 1. Verificar permiso
if not can_create_resource(user_id, tenant_id, 'vacancy'):
    return jsonify({'error': 'No tienes permisos para crear vacantes'}), 403

# 2. Agregar created_by_user al INSERT
sql = """
    INSERT INTO Vacantes (
        id_cliente, cargo_solicitado, descripcion, ciudad, requisitos, 
        salario_min, salario_max, salario, fecha_apertura, estado, tenant_id, created_by_user
    ) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURDATE(), 'Abierta', %s, %s)
"""
cursor.execute(sql, (..., tenant_id, user_id))
```

---

### 3. **DELETE /api/vacancies/<id>** (líneas 5528-5575)
**Función:** `delete_vacancy(id_vacante)`

**Situación actual:**
```python
cursor.execute("""
    SELECT id_vacante, cargo_solicitado, estado 
    FROM Vacantes 
    WHERE id_vacante = %s AND tenant_id = %s
""", (id_vacante, tenant_id))
```

**Problema:** ❌ No verifica si el usuario tiene acceso a la vacante

**Solución:**
```python
from permission_service import can_access_resource

user_id = g.current_user['user_id']

# Verificar acceso con permiso de escritura/full
if not can_access_resource(user_id, tenant_id, 'vacancy', id_vacante, 'full'):
    return jsonify({'error': 'No tienes acceso a esta vacante'}), 403
```

---

### 4. **PUT /api/vacancies/<id>/status** (líneas 5577-5598)
**Función:** `update_vacancy_status(id_vacante)`

**Situación actual:**
```python
cursor.execute("""
    UPDATE Vacantes SET estado = %s WHERE id_vacante = %s
""", (nuevo_estado, id_vacante))
```

**Problema:** ❌ No verifica tenant_id ni acceso del usuario

**Solución:**
```python
from permission_service import can_access_resource

user_id = g.current_user['user_id']
tenant_id = get_current_tenant_id()

# Verificar acceso con permiso de escritura
if not can_access_resource(user_id, tenant_id, 'vacancy', id_vacante, 'write'):
    return jsonify({'error': 'No tienes acceso a esta vacante'}), 403

# Agregar tenant_id al UPDATE
cursor.execute("""
    UPDATE Vacantes 
    SET estado = %s 
    WHERE id_vacante = %s AND tenant_id = %s
""", (nuevo_estado, id_vacante, tenant_id))
```

---

### 5. **GET /api/vacancies/<id>/pipeline** (líneas 3516-3565)
**Función:** `get_vacancy_pipeline(id_vacante)`

**Situación actual:**
```python
user_role = getattr(g, 'current_user', {}).get('rol', '')

if user_role == 'Administrador':  # ❌ Compara string
    cursor.execute("SELECT id_vacante FROM Vacantes WHERE id_vacante = %s", (id_vacante,))
else:
    cursor.execute("SELECT id_vacante FROM Vacantes WHERE id_vacante = %s AND tenant_id = %s", (id_vacante, tenant_id))
```

**Problema:** 
- ❌ Compara rol como string
- ❌ No verifica acceso del usuario a la vacante

**Solución:**
```python
from permission_service import can_access_resource

user_id = g.current_user['user_id']

# Verificar acceso a la vacante
if not can_access_resource(user_id, tenant_id, 'vacancy', id_vacante, 'read'):
    return jsonify({'error': 'No tienes acceso a esta vacante'}), 403
```

---

## 🔧 CAMBIOS NECESARIOS

### **Archivo:** `bACKEND/app.py`

#### Cambio 1: Modificar GET `/api/vacancies`
- Reemplazar lógica de rol por `build_user_filter_condition()`
- Filtrar por tenant_id correctamente
- Agregar filtro por usuario según rol
- **Líneas:** 5373-5438

#### Cambio 2: Modificar POST `/api/vacancies`
- Verificar permiso de creación
- Agregar `created_by_user` en INSERT
- **Líneas:** 5439-5524

#### Cambio 3: Modificar DELETE `/api/vacancies/<id>`
- Verificar acceso con `can_access_resource()`
- Solo Admin o creador pueden eliminar
- **Líneas:** 5528-5575

#### Cambio 4: Modificar PUT `/api/vacancies/<id>/status`
- Verificar acceso con `can_access_resource()`
- Agregar tenant_id al UPDATE
- **Líneas:** 5577-5598

#### Cambio 5: Modificar GET `/api/vacancies/<id>/pipeline`
- Reemplazar lógica de rol
- Verificar acceso con `can_access_resource()`
- **Líneas:** 3516-3565

---

## ⚠️ CONSIDERACIONES

### **Compatibilidad:**
- Vacantes existentes sin `created_by_user` (NULL) → accesibles por todos

### **Lógica de GROUP BY:**
- Cuidado al insertar condiciones WHERE antes de GROUP BY
- Usar `.replace()` o reescribir query completa

### **Filtro de Cliente vs Tenant:**
- El código actual confunde `id_cliente` (empresa que busca personal) con `tenant_id` (empresa reclutadora)
- **CORRECTO:** `WHERE V.tenant_id = %s` (empresa reclutadora)
- **INCORRECTO:** `WHERE V.id_cliente = %s` (empresa cliente)

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Modificar `GET /api/vacancies` con filtro por usuario
- [ ] Modificar `POST /api/vacancies` con verificación y `created_by_user`
- [ ] Modificar `DELETE /api/vacancies/<id>` con verificación de acceso
- [ ] Modificar `PUT /api/vacancies/<id>/status` con verificación de acceso
- [ ] Modificar `GET /api/vacancies/<id>/pipeline` con verificación de acceso
- [ ] Testing con usuarios de diferentes roles

---

## 📊 MATRIZ DE PERMISOS ESPERADA

| Acción | Admin | Supervisor | Reclutador |
|--------|-------|------------|------------|
| **Ver todas las vacantes** | ✅ | ❌ | ❌ |
| **Ver vacantes del equipo** | ✅ | ✅ | ❌ |
| **Ver vacantes propias** | ✅ | ✅ | ✅ |
| **Crear vacante** | ✅ | ✅ | ✅ |
| **Editar vacante propia** | ✅ | ✅ | ✅ |
| **Editar vacante del equipo** | ✅ | ✅ | ❌ |
| **Eliminar vacante propia** | ✅ | ✅ | ✅ |
| **Eliminar vacante ajena** | ✅ | ❌ | ❌ |
| **Ver pipeline de vacante propia** | ✅ | ✅ | ✅ |
| **Ver pipeline de vacante ajena** | ✅ | ✅ (equipo) | ❌ |

---

**Tiempo estimado:** 1-2 horas  
**Riesgo:** Medio (query con GROUP BY requiere cuidado)

**Próximo paso:** Implementar cambios en `app.py` 🚀

