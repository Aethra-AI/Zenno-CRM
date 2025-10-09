# ✅ MÓDULO B4 - PERMISSION SERVICE COMPLETADO

**Fecha:** Octubre 9, 2025  
**Archivo:** `bACKEND/permission_service.py`  
**Estado:** 🟢 Listo para integrar

---

## 📋 LO QUE SE CREÓ

### **Archivo nuevo:** `permission_service.py` (540 líneas)

**Funcionalidades implementadas:**

#### 1. **Gestión de Roles** (7 funciones)
- `get_user_role_info()` - Info completa del rol
- `get_user_role_name()` - Nombre del rol
- `is_admin()` - Verifica si es Admin
- `is_supervisor()` - Verifica si es Supervisor
- `is_recruiter()` - Verifica si es Reclutador

#### 2. **Gestión de Permisos** (3 funciones)
- `check_permission()` - Verifica permisos específicos
- `get_user_permissions()` - Obtiene todos los permisos

#### 3. **Jerarquía de Equipos** (3 funciones)
- `get_team_members()` - Miembros del equipo del supervisor
- `is_user_in_team()` - Verifica si usuario está en equipo
- `get_user_supervisor()` - Obtiene supervisor del usuario

#### 4. **Acceso a Recursos** (4 funciones)
- `get_assigned_resources()` - Recursos asignados al usuario
- `can_access_resource()` - Verifica acceso a recurso específico
- `was_created_by_user()` - Verifica si usuario creó el recurso

#### 5. **Filtros Dinámicos** (2 funciones)
- `get_accessible_user_ids()` - IDs de usuarios que puede ver
- `build_user_filter_condition()` - Construye condición SQL

#### 6. **Permisos Específicos** (4 funciones)
- `can_create_resource()` - Puede crear recursos
- `can_manage_users()` - Puede gestionar usuarios
- `can_assign_resources()` - Puede asignar recursos
- `can_view_reports()` - Puede ver reportes

---

## 🎯 EJEMPLOS DE USO

### **Ejemplo 1: Verificar Rol**

```python
from permission_service import is_admin, is_supervisor, get_user_role_name

# Verificar si es admin
if is_admin(user_id, tenant_id):
    print("Usuario es Administrador")

# Obtener nombre del rol
role = get_user_role_name(user_id, tenant_id)
print(f"Rol: {role}")  # "Administrador", "Supervisor", "Reclutador"
```

---

### **Ejemplo 2: Verificar Permisos**

```python
from permission_service import check_permission, can_create_resource

# Verificar permiso específico
if check_permission(user_id, tenant_id, 'manage_users'):
    # Usuario puede gestionar otros usuarios
    pass

# Verificar si puede crear vacantes
if can_create_resource(user_id, tenant_id, 'vacancy'):
    # Crear vacante...
    pass
```

---

### **Ejemplo 3: Obtener Equipo del Supervisor**

```python
from permission_service import get_team_members, is_user_in_team

# Obtener miembros del equipo
team_ids = get_team_members(supervisor_id, tenant_id)
print(f"Equipo: {team_ids}")  # [5, 8, 12]

# Verificar si usuario está en el equipo
if is_user_in_team(supervisor_id, team_member_id, tenant_id):
    print("Usuario está en el equipo")
```

---

### **Ejemplo 4: Verificar Acceso a Recurso**

```python
from permission_service import can_access_resource, was_created_by_user

# Verificar si puede editar un candidato
if can_access_resource(user_id, tenant_id, 'candidate', 123, 'write'):
    # Editar candidato 123
    pass

# Verificar si usuario creó la vacante
if was_created_by_user(user_id, tenant_id, 'vacancy', 45):
    print("Usuario creó esta vacante")
```

---

### **Ejemplo 5: Filtrar Query por Usuario** ⭐

```python
from permission_service import build_user_filter_condition

# Obtener condición de filtro
condition, params = build_user_filter_condition(user_id, tenant_id)

# Construir query
if condition:
    # Reclutador o Supervisor: filtrar por usuario
    query = f"""
        SELECT * FROM Vacantes 
        WHERE tenant_id = %s AND {condition}
        ORDER BY fecha_creacion DESC
    """
    cursor.execute(query, [tenant_id] + params)
else:
    # Admin: sin filtro adicional
    query = """
        SELECT * FROM Vacantes 
        WHERE tenant_id = %s
        ORDER BY fecha_creacion DESC
    """
    cursor.execute(query, [tenant_id])

results = cursor.fetchall()
```

**Resultado:**
- **Admin:** Ve TODAS las vacantes del tenant
- **Supervisor (ID 5, equipo [8, 12]):** 
  - Query: `WHERE tenant_id = 1 AND created_by_user IN (5, 8, 12)`
  - Ve sus vacantes + las de su equipo
- **Reclutador (ID 8):**
  - Query: `WHERE tenant_id = 1 AND created_by_user = 8`
  - Solo ve sus propias vacantes

---

## 🔧 INTEGRACIÓN EN ENDPOINTS

### **Ejemplo: Endpoint GET /api/candidates**

**ANTES (sin permisos):**
```python
@app.route('/api/candidates', methods=['GET'])
@token_required
def get_candidates():
    tenant_id = get_current_tenant_id()
    
    # Todos ven todos los candidatos del tenant
    cursor.execute("""
        SELECT * FROM Afiliados 
        WHERE tenant_id = %s
    """, (tenant_id,))
    
    return jsonify(cursor.fetchall())
```

**DESPUÉS (con permisos):**
```python
from permission_service import build_user_filter_condition

@app.route('/api/candidates', methods=['GET'])
@token_required
def get_candidates():
    user_data = g.current_user
    user_id = user_data['user_id']
    tenant_id = g.current_tenant_id
    
    # Construir filtro según rol
    condition, params = build_user_filter_condition(user_id, tenant_id)
    
    if condition:
        query = f"""
            SELECT * FROM Afiliados 
            WHERE tenant_id = %s AND {condition}
            ORDER BY fecha_registro DESC
        """
        cursor.execute(query, [tenant_id] + params)
    else:
        query = """
            SELECT * FROM Afiliados 
            WHERE tenant_id = %s
            ORDER BY fecha_registro DESC
        """
        cursor.execute(query, [tenant_id])
    
    return jsonify(cursor.fetchall())
```

---

### **Ejemplo: Endpoint POST /api/vacancies**

```python
from permission_service import can_create_resource

@app.route('/api/vacancies', methods=['POST'])
@token_required
def create_vacancy():
    user_data = g.current_user
    user_id = user_data['user_id']
    tenant_id = g.current_tenant_id
    
    # Verificar permiso de creación
    if not can_create_resource(user_id, tenant_id, 'vacancy'):
        return jsonify({
            'error': 'No tienes permisos para crear vacantes'
        }), 403
    
    data = request.get_json()
    
    # Crear vacante con created_by_user
    cursor.execute("""
        INSERT INTO Vacantes 
        (cargo_solicitado, id_cliente, tenant_id, created_by_user)
        VALUES (%s, %s, %s, %s)
    """, (data['cargo'], data['id_cliente'], tenant_id, user_id))
    
    conn.commit()
    
    return jsonify({'success': True, 'id': cursor.lastrowid}), 201
```

---

### **Ejemplo: Endpoint PUT /api/candidates/<id>**

```python
from permission_service import can_access_resource

@app.route('/api/candidates/<int:id_afiliado>', methods=['PUT'])
@token_required
def update_candidate(id_afiliado):
    user_data = g.current_user
    user_id = user_data['user_id']
    tenant_id = g.current_tenant_id
    
    # Verificar acceso de escritura
    if not can_access_resource(user_id, tenant_id, 'candidate', id_afiliado, 'write'):
        return jsonify({
            'error': 'No tienes permisos para editar este candidato'
        }), 403
    
    data = request.get_json()
    
    # Actualizar candidato...
    cursor.execute("""
        UPDATE Afiliados 
        SET nombre_completo = %s, telefono = %s
        WHERE id_afiliado = %s AND tenant_id = %s
    """, (data['nombre'], data['telefono'], id_afiliado, tenant_id))
    
    conn.commit()
    
    return jsonify({'success': True}), 200
```

---

## 📊 MATRIZ DE PERMISOS

| Acción | Administrador | Supervisor | Reclutador |
|--------|---------------|------------|------------|
| **Ver todos los recursos** | ✅ Sí | ❌ No | ❌ No |
| **Ver recursos del equipo** | ✅ Sí | ✅ Sí (su equipo) | ❌ No |
| **Ver recursos propios** | ✅ Sí | ✅ Sí | ✅ Sí |
| **Crear recursos** | ✅ Sí | ✅ Sí | ✅ Sí |
| **Editar recursos propios** | ✅ Sí | ✅ Sí | ✅ Sí |
| **Editar recursos del equipo** | ✅ Sí | ✅ Sí | ❌ No |
| **Editar cualquier recurso** | ✅ Sí | ❌ No | ❌ No |
| **Eliminar recursos** | ✅ Sí | ✅ Sí (propios) | ✅ Sí (propios) |
| **Gestionar usuarios** | ✅ Sí | ❌ No | ❌ No |
| **Asignar recursos** | ✅ Sí | ✅ Sí (a su equipo) | ❌ No |
| **Ver reportes globales** | ✅ Sí | ❌ No | ❌ No |
| **Ver reportes del equipo** | ✅ Sí | ✅ Sí | ❌ No |
| **Ver reportes propios** | ✅ Sí | ✅ Sí | ✅ Sí |

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### **Completado:**
- [x] Crear `permission_service.py`
- [x] Funciones de roles
- [x] Funciones de permisos
- [x] Funciones de jerarquía
- [x] Funciones de acceso a recursos
- [x] Filtros dinámicos
- [x] Documentación

### **Pendiente (Próximos Módulos):**
- [ ] Integrar en endpoints existentes (Módulo B5-B17)
- [ ] Crear decorador `@require_permission()` (Módulo B7)
- [ ] Agregar tests unitarios
- [ ] Crear endpoints de gestión de equipos
- [ ] Crear endpoints de asignación de recursos

---

## 🚀 SIGUIENTE PASO: MÓDULO B5

**Objetivo:** Aplicar el servicio de permisos a los endpoints de candidatos

**Tareas:**
1. Modificar `GET /api/candidates` para filtrar por usuario
2. Modificar `POST /api/candidates` para agregar `created_by_user`
3. Modificar `PUT /api/candidates/<id>` para verificar acceso
4. Modificar `DELETE /api/candidates/<id>` para verificar acceso
5. Testing con usuarios de diferentes roles

**Tiempo estimado:** 2-3 horas

---

### ❓ **¿CONTINUAMOS CON B5 O QUIERES PROBAR B4 PRIMERO?**

Opciones:
1. **Probar B4:** Crear datos de prueba y verificar que funciona
2. **Continuar con B5:** Empezar a integrar en endpoints
3. **Revisar algo más de B4**

**¿Qué prefieres?** 🎯


