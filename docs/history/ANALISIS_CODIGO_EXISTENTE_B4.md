# 🔍 ANÁLISIS DEL CÓDIGO EXISTENTE - MÓDULO B4

**Fecha:** Octubre 9, 2025  
**Objetivo:** Revisar el backend actual antes de implementar el sistema de permisos

---

## 📋 LO QUE YA EXISTE

### 1. **Autenticación JWT** ✅

**Ubicación:** `bACKEND/app.py` (líneas 392-461)

```python
@wraps(f)
def token_required(f):
    """Decorador para verificar token JWT"""
    # Extrae token del header Authorization
    # Decodifica JWT con SECRET_KEY
    # Almacena en contexto:
    #   - g.current_tenant_id
    #   - g.current_user (dict con user_id, tenant_id, rol, etc.)
```

**Características:**
- ✅ Valida que el token sea válido
- ✅ Extrae `tenant_id` del token
- ✅ Almacena datos del usuario en `g.current_user`
- ❌ **NO valida permisos específicos**
- ❌ **NO valida jerarquía de usuarios**
- ❌ **NO verifica acceso a recursos**

---

### 2. **Endpoint de Login** ✅

**Ubicación:** `bACKEND/app.py` (líneas 143-383)

```python
@app.route('/api/auth/login', methods=['POST'])
def login():
    # Valida credenciales
    # Genera JWT token
    # Retorna:
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'nombre': user['nombre'],
            'email': user['email'],
            'rol': user['rol_nombre'],           # ← ROL ACTUAL
            'tenant_id': user['tenant_id'],      # ← TENANT
            'permisos': json.loads(user['permisos'])  # ← PERMISOS JSON
        }
    })
```

**Características:**
- ✅ Devuelve el rol del usuario
- ✅ Devuelve permisos en formato JSON
- ✅ Incluye `tenant_id` en el token
- ✅ Registra sesión en `UserSessions`

**Query actual:**
```sql
SELECT 
    u.id, 
    u.nombre, 
    u.email, 
    u.password, 
    u.activo,
    u.tenant_id,
    u.id_cliente,
    c.empresa_nombre,
    r.nombre as rol_nombre,
    r.permisos              -- ← Permisos del rol
FROM Users u
LEFT JOIN Roles r ON u.role_id = r.id
LEFT JOIN Clientes c ON u.id_cliente = c.id_cliente
WHERE u.email = %s
```

---

### 3. **Funciones Auxiliares Multi-Tenancy** ✅

**Ubicación:** `bACKEND/app.py` (líneas 464-536)

```python
def get_current_tenant_id():
    """Obtiene tenant_id del contexto (g)"""
    return getattr(g, 'current_tenant_id', None)

def add_tenant_filter(base_query, table_alias='', tenant_column='tenant_id'):
    """Agrega filtro WHERE tenant_id = %s a queries"""
    tenant_id = get_current_tenant_id()
    # Retorna (query_modificada, tenant_id)
```

**Características:**
- ✅ Filtrado automático por `tenant_id`
- ❌ **NO filtra por `created_by_user`**
- ❌ **NO valida permisos de usuario**

---

### 4. **Endpoints Protegidos** ⚠️

**Patrón actual:**
```python
@app.route('/api/candidates', methods=['GET'])
@token_required  # ← Solo valida token, NO permisos
def get_candidates():
    tenant_id = get_current_tenant_id()
    # Query filtra por tenant_id
    # PERO NO por usuario ni permisos
```

**Ejemplos de endpoints:**
- `/api/candidates` (GET, POST)
- `/api/applications` (GET, POST, PUT)
- `/api/interviews` (GET, POST, DELETE)
- `/api/vacancies` (GET, POST, PUT, DELETE)
- `/api/clients` (GET, POST, PUT)
- `/api/hired` (GET, POST)

**Problema:**
- ❌ Todos los usuarios del mismo tenant ven TODOS los datos
- ❌ No hay control de quién creó qué
- ❌ No hay jerarquía (Admin vs Reclutador)

---

## ❌ LO QUE FALTA (Para Módulo B4)

### 1. **Servicio de Permisos**

**Archivo nuevo:** `bACKEND/permission_service.py`

**Funciones necesarias:**
```python
def check_permission(user_id, tenant_id, permission_key):
    """Verifica si usuario tiene un permiso específico"""
    
def can_access_resource(user_id, tenant_id, resource_type, resource_id):
    """Verifica si usuario puede acceder a un recurso"""
    
def get_user_role(user_id, tenant_id):
    """Obtiene el rol del usuario en el tenant"""
    
def is_admin(user_id, tenant_id):
    """Verifica si usuario es Admin"""
    
def is_supervisor(user_id, tenant_id):
    """Verifica si usuario es Supervisor"""
    
def get_team_members(supervisor_id, tenant_id):
    """Obtiene miembros del equipo de un supervisor"""
    
def get_accessible_resources(user_id, tenant_id, resource_type):
    """Obtiene IDs de recursos accesibles para el usuario"""
```

---

### 2. **Nuevo Decorador de Permisos**

**Archivo:** `bACKEND/app.py` (agregar)

```python
def require_permission(permission_key):
    """
    Decorador para validar permisos específicos.
    Uso: @require_permission('create_vacancy')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_data = g.current_user
            tenant_id = g.current_tenant_id
            
            if not check_permission(user_data['user_id'], tenant_id, permission_key):
                return jsonify({
                    'error': 'No tienes permisos para esta acción',
                    'required_permission': permission_key
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator
```

**Uso futuro:**
```python
@app.route('/api/vacancies', methods=['POST'])
@token_required
@require_permission('create_vacancy')  # ← NUEVO
def create_vacancy():
    # Solo Admin y Supervisor pueden crear vacantes
    pass
```

---

### 3. **Helper para Filtros Dinámicos**

```python
def build_user_filter(base_query, user_id, tenant_id, resource_table=''):
    """
    Construye filtro SQL considerando rol del usuario:
    - Admin: ve todo del tenant
    - Supervisor: ve su equipo + recursos asignados
    - Reclutador: solo sus propios recursos
    """
    role = get_user_role(user_id, tenant_id)
    
    if role == 'Administrador':
        # Sin filtro adicional (ve todo del tenant)
        return base_query
    
    elif role == 'Supervisor':
        # Ve su equipo + recursos asignados
        team_ids = get_team_members(user_id, tenant_id)
        # Agregar filtro: created_by_user IN (user_id, team_ids)
        
    elif role == 'Reclutador':
        # Solo sus propios recursos
        # Agregar filtro: created_by_user = user_id
```

---

## 🎯 PLAN DE IMPLEMENTACIÓN B4

### **Fase 1: Crear Servicio Base** (1-2 horas)
1. Crear `permission_service.py`
2. Implementar funciones de verificación
3. Implementar queries a las nuevas tablas

### **Fase 2: Decorador de Permisos** (30 min)
1. Crear `require_permission()` en `app.py`
2. Probar con un endpoint simple

### **Fase 3: Helper de Filtros** (1 hora)
1. Crear `build_user_filter()`
2. Integrar con queries existentes

### **Fase 4: Testing** (1 hora)
1. Crear usuarios de prueba (Admin, Supervisor, Reclutador)
2. Probar acceso a recursos
3. Validar jerarquía

---

## 📊 RESUMEN

| Componente | Estado | Acción |
|------------|--------|--------|
| JWT Auth | ✅ Existe | Reutilizar |
| Token Validation | ✅ Existe | Reutilizar |
| Tenant Isolation | ✅ Existe | Mantener |
| User Permissions | ❌ Falta | **Crear B4** |
| Role Hierarchy | ❌ Falta | **Crear B4** |
| Resource Access | ❌ Falta | **Crear B4** |
| Permission Decorator | ❌ Falta | **Crear B4** |
| User Filters | ❌ Falta | **Crear B4** |

---

## ✅ CONCLUSIÓN

**Lo bueno:**
- Ya tenemos JWT y autenticación funcional
- Multi-tenancy bien implementado
- Estructura de roles en BD

**Lo que agregaremos:**
- Servicio de permisos (`permission_service.py`)
- Decorador de permisos (`@require_permission`)
- Lógica de jerarquía (Admin > Supervisor > Reclutador)
- Filtros por usuario en queries

**Ventaja:**
- **NO necesitamos reescribir el sistema de autenticación**
- **Solo agregamos una capa de permisos encima**

---

**Próximo paso:** Crear `permission_service.py` 🚀


