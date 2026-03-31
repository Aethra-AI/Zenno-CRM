# 🔍 MÓDULO B16 - GESTIÓN DE EQUIPOS - ANÁLISIS COMPLETO

**Fecha:** Octubre 9, 2025  
**Estado:** Análisis completo - Listo para implementar

---

## 📋 RESUMEN EJECUTIVO

**B16** es el **ÚLTIMO módulo de backend** y el más importante para el sistema de jerarquías.

**Objetivo:** Crear endpoints para que Admins y Supervisores puedan:
- Ver su equipo
- Agregar miembros a su equipo
- Remover miembros de su equipo
- Listar usuarios disponibles para agregar

**Complejidad:** ALTA  
**Tiempo estimado:** 2-3 horas

---

## 🎯 CONTEXTO: ¿QUÉ ES Team_Structure?

### **Tabla creada en B1:**
```sql
CREATE TABLE Team_Structure (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    supervisor_id INT NOT NULL,      -- Supervisor del equipo
    team_member_id INT NOT NULL,     -- Miembro del equipo
    assigned_by INT NULL,            -- Quién lo asignó
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id),
    FOREIGN KEY (supervisor_id) REFERENCES Users(id),
    FOREIGN KEY (team_member_id) REFERENCES Users(id),
    FOREIGN KEY (assigned_by) REFERENCES Users(id)
)
```

### **Relaciones:**
```
Supervisor (ID: 5)
    ├── Miembro 1 (ID: 8)   ← Reclutador
    ├── Miembro 2 (ID: 12)  ← Reclutador
    └── Miembro 3 (ID: 15)  ← Reclutador
```

---

## 🔧 ENDPOINTS A CREAR

### **1. GET `/api/teams/my-team`**
**Descripción:** Obtener miembros del equipo del supervisor actual

**Quién puede usarlo:**
- ✅ Supervisores (ven su equipo)
- ✅ Admins (ven todos los equipos)
- ❌ Reclutadores (403)

**Query esperado:**
```sql
-- Para Supervisor (ID 5):
SELECT 
    u.id, u.nombre, u.email, u.telefono, u.activo,
    r.nombre as rol_nombre,
    ts.assigned_at,
    ts.id as team_structure_id
FROM Team_Structure ts
JOIN Users u ON ts.team_member_id = u.id
LEFT JOIN Roles r ON u.rol_id = r.id
WHERE ts.supervisor_id = 5 
AND ts.tenant_id = 1
AND ts.is_active = TRUE
ORDER BY ts.assigned_at DESC
```

**Respuesta esperada:**
```json
{
  "success": true,
  "supervisor": {
    "id": 5,
    "nombre": "María Supervisor",
    "email": "maria@empresa.com"
  },
  "team_members": [
    {
      "id": 8,
      "nombre": "Carlos Reclutador",
      "email": "carlos@empresa.com",
      "rol_nombre": "Reclutador",
      "assigned_at": "2025-10-01T10:00:00",
      "team_structure_id": 1
    },
    {
      "id": 12,
      "nombre": "Ana Reclutadora",
      "email": "ana@empresa.com",
      "rol_nombre": "Reclutador",
      "assigned_at": "2025-10-02T14:30:00",
      "team_structure_id": 2
    }
  ],
  "total_members": 2
}
```

---

### **2. POST `/api/teams/members`**
**Descripción:** Agregar un miembro al equipo

**Quién puede usarlo:**
- ✅ Supervisores (agregan a SU equipo)
- ✅ Admins (agregan a cualquier equipo)
- ❌ Reclutadores (403)

**Request body:**
```json
{
  "team_member_id": 15,
  "supervisor_id": 5  // Solo para admins (opcional)
}
```

**Validaciones:**
1. ✅ El miembro debe existir y estar activo
2. ✅ El miembro debe pertenecer al mismo tenant
3. ✅ El miembro NO debe estar ya en el equipo
4. ✅ El miembro debe ser Reclutador (no puede ser Admin o Supervisor)
5. ✅ El supervisor debe ser realmente Supervisor
6. ✅ Supervisor solo puede agregar a SU equipo
7. ✅ Admin puede agregar a cualquier equipo

**Query de inserción:**
```sql
INSERT INTO Team_Structure 
(tenant_id, supervisor_id, team_member_id, assigned_by, is_active)
VALUES (%s, %s, %s, %s, TRUE)
```

**Respuesta esperada:**
```json
{
  "success": true,
  "message": "Miembro agregado al equipo exitosamente",
  "team_structure_id": 3,
  "member": {
    "id": 15,
    "nombre": "Pedro Reclutador",
    "email": "pedro@empresa.com"
  }
}
```

---

### **3. DELETE `/api/teams/members/<int:team_member_id>`**
**Descripción:** Remover un miembro del equipo

**Quién puede usarlo:**
- ✅ Supervisores (remueven de SU equipo)
- ✅ Admins (remueven de cualquier equipo)
- ❌ Reclutadores (403)

**Validaciones:**
1. ✅ El miembro debe estar en el equipo
2. ✅ Supervisor solo puede remover de SU equipo
3. ✅ Admin puede remover de cualquier equipo

**Método:** Soft delete (marcar `is_active = FALSE`)

**Query de eliminación:**
```sql
-- Soft delete:
UPDATE Team_Structure 
SET is_active = FALSE 
WHERE team_member_id = %s 
AND supervisor_id = %s 
AND tenant_id = %s
AND is_active = TRUE
```

**Respuesta esperada:**
```json
{
  "success": true,
  "message": "Miembro removido del equipo exitosamente"
}
```

---

### **4. GET `/api/teams/available-members`**
**Descripción:** Obtener lista de usuarios disponibles para agregar al equipo

**Quién puede usarlo:**
- ✅ Supervisores (ven reclutadores disponibles para SU equipo)
- ✅ Admins (ven todos los reclutadores disponibles)

**Query esperado:**
```sql
-- Para Supervisor (ID 5):
SELECT 
    u.id, u.nombre, u.email, u.telefono,
    r.nombre as rol_nombre
FROM Users u
LEFT JOIN Roles r ON u.rol_id = r.id
LEFT JOIN Team_Structure ts ON u.id = ts.team_member_id 
    AND ts.supervisor_id = 5 
    AND ts.is_active = TRUE
WHERE u.tenant_id = 1
AND u.activo = TRUE
AND r.nombre = 'Reclutador'  -- Solo reclutadores
AND ts.id IS NULL  -- No están en el equipo
ORDER BY u.nombre
```

**Respuesta esperada:**
```json
{
  "success": true,
  "available_members": [
    {
      "id": 20,
      "nombre": "Luis Reclutador",
      "email": "luis@empresa.com",
      "telefono": "12345678",
      "rol_nombre": "Reclutador"
    },
    {
      "id": 25,
      "nombre": "Sofia Reclutadora",
      "email": "sofia@empresa.com",
      "telefono": "87654321",
      "rol_nombre": "Reclutador"
    }
  ],
  "total": 2
}
```

---

### **5. GET `/api/teams/all` (Opcional - solo Admins)**
**Descripción:** Ver TODOS los equipos del tenant

**Quién puede usarlo:**
- ✅ Solo Admins
- ❌ Supervisores (403)
- ❌ Reclutadores (403)

**Query esperado:**
```sql
SELECT 
    s.id as supervisor_id,
    s.nombre as supervisor_nombre,
    s.email as supervisor_email,
    COUNT(ts.id) as total_members,
    GROUP_CONCAT(u.nombre SEPARATOR ', ') as members_names
FROM Users s
LEFT JOIN Team_Structure ts ON s.id = ts.supervisor_id 
    AND ts.is_active = TRUE
    AND ts.tenant_id = 1
LEFT JOIN Users u ON ts.team_member_id = u.id
LEFT JOIN Roles r ON s.rol_id = r.id
WHERE s.tenant_id = 1
AND s.activo = TRUE
AND r.nombre = 'Supervisor'
GROUP BY s.id, s.nombre, s.email
ORDER BY total_members DESC
```

**Respuesta esperada:**
```json
{
  "success": true,
  "teams": [
    {
      "supervisor_id": 5,
      "supervisor_nombre": "María Supervisor",
      "supervisor_email": "maria@empresa.com",
      "total_members": 3,
      "members_names": "Carlos, Ana, Pedro"
    },
    {
      "supervisor_id": 10,
      "supervisor_nombre": "Juan Supervisor",
      "supervisor_email": "juan@empresa.com",
      "total_members": 2,
      "members_names": "Luis, Sofia"
    }
  ],
  "total_teams": 2
}
```

---

## 🔒 PERMISOS Y VALIDACIONES

### **Matriz de permisos:**

| Endpoint | Admin | Supervisor | Reclutador |
|----------|-------|------------|------------|
| GET `/api/teams/my-team` | ✅ (todos) | ✅ (su equipo) | ❌ 403 |
| POST `/api/teams/members` | ✅ (cualquier equipo) | ✅ (su equipo) | ❌ 403 |
| DELETE `/api/teams/members/<id>` | ✅ (cualquier equipo) | ✅ (su equipo) | ❌ 403 |
| GET `/api/teams/available-members` | ✅ | ✅ | ❌ 403 |
| GET `/api/teams/all` | ✅ | ❌ 403 | ❌ 403 |

---

### **Validaciones críticas:**

#### **1. Solo Reclutadores pueden ser miembros de equipo:**
```python
# Verificar que el rol del miembro es "Reclutador"
cursor.execute("""
    SELECT r.nombre 
    FROM Users u
    JOIN Roles r ON u.rol_id = r.id
    WHERE u.id = %s AND u.tenant_id = %s
""", (team_member_id, tenant_id))
role = cursor.fetchone()
if not role or role['nombre'] != 'Reclutador':
    return jsonify({'error': 'Solo reclutadores pueden ser miembros de equipo'}), 400
```

#### **2. Supervisor no puede agregar a equipo ajeno:**
```python
# Si es supervisor, verificar que está agregando a SU equipo
if user_role == 'Supervisor':
    if supervisor_id and supervisor_id != user_id:
        return jsonify({'error': 'No puedes agregar miembros a otro equipo'}), 403
    supervisor_id = user_id  # Forzar a su propio ID
```

#### **3. Evitar duplicados:**
```python
# Verificar que el miembro no esté ya en el equipo
cursor.execute("""
    SELECT id FROM Team_Structure 
    WHERE supervisor_id = %s 
    AND team_member_id = %s 
    AND is_active = TRUE
    AND tenant_id = %s
""", (supervisor_id, team_member_id, tenant_id))
if cursor.fetchone():
    return jsonify({'error': 'El miembro ya está en el equipo'}), 409
```

---

## 🧪 CASOS DE PRUEBA

### **Test 1: Supervisor ve su equipo**

**Usuario:** Supervisor ID 5 (equipo: [8, 12])

**Request:**
```http
GET /api/teams/my-team
Authorization: Bearer <token_supervisor_5>
```

**Resultado esperado:**
```json
{
  "success": true,
  "team_members": [
    {"id": 8, "nombre": "Carlos..."},
    {"id": 12, "nombre": "Ana..."}
  ],
  "total_members": 2
}
```

---

### **Test 2: Supervisor agrega miembro a su equipo**

**Usuario:** Supervisor ID 5

**Request:**
```http
POST /api/teams/members
Authorization: Bearer <token_supervisor_5>
Content-Type: application/json

{
  "team_member_id": 15
}
```

**Validaciones:**
1. ✅ Usuario 15 existe y es Reclutador
2. ✅ Usuario 15 NO está ya en el equipo
3. ✅ Se crea registro en Team_Structure

**Resultado esperado:**
```json
{
  "success": true,
  "message": "Miembro agregado al equipo exitosamente",
  "team_structure_id": 3
}
```

---

### **Test 3: Supervisor intenta agregar a equipo ajeno (DENEGADO)**

**Usuario:** Supervisor ID 5

**Request:**
```http
POST /api/teams/members
Authorization: Bearer <token_supervisor_5>
Content-Type: application/json

{
  "team_member_id": 20,
  "supervisor_id": 10  // ← Intenta agregar a equipo de ID 10
}
```

**Resultado esperado:**
```json
{
  "error": "No puedes agregar miembros a otro equipo"
}
```
**Código HTTP:** `403 Forbidden`

---

### **Test 4: Reclutador intenta ver equipos (DENEGADO)**

**Usuario:** Reclutador ID 8

**Request:**
```http
GET /api/teams/my-team
Authorization: Bearer <token_reclutador_8>
```

**Resultado esperado:**
```json
{
  "error": "No tienes permisos para ver equipos"
}
```
**Código HTTP:** `403 Forbidden`

---

### **Test 5: Admin agrega miembro a cualquier equipo**

**Usuario:** Admin ID 1

**Request:**
```http
POST /api/teams/members
Authorization: Bearer <token_admin_1>
Content-Type: application/json

{
  "team_member_id": 25,
  "supervisor_id": 10  // ← Admin PUEDE especificar otro supervisor
}
```

**Resultado esperado:**
```json
{
  "success": true,
  "message": "Miembro agregado al equipo exitosamente"
}
```

---

### **Test 6: Intento de agregar Admin como miembro (DENEGADO)**

**Usuario:** Admin ID 1

**Request:**
```http
POST /api/teams/members
Content-Type: application/json

{
  "team_member_id": 2,  // ← Usuario 2 es Admin
  "supervisor_id": 5
}
```

**Resultado esperado:**
```json
{
  "error": "Solo reclutadores pueden ser miembros de equipo"
}
```
**Código HTTP:** `400 Bad Request`

---

### **Test 7: Supervisor remueve miembro de su equipo**

**Usuario:** Supervisor ID 5

**Request:**
```http
DELETE /api/teams/members/8
Authorization: Bearer <token_supervisor_5>
```

**Resultado esperado:**
```json
{
  "success": true,
  "message": "Miembro removido del equipo exitosamente"
}
```

**Verificación en BD:**
```sql
-- Antes:
SELECT * FROM Team_Structure WHERE id = 1;
-- team_member_id: 8, is_active: TRUE

-- Después:
SELECT * FROM Team_Structure WHERE id = 1;
-- team_member_id: 8, is_active: FALSE ← Soft delete
```

---

## 📊 IMPACTO EN PERMISOS EXISTENTES

### **¿Cómo se usan estos equipos?**

Los equipos creados aquí se usan en **`permission_service.py`** para determinar qué puede ver cada usuario.

**Función clave: `get_team_members()`**

```python
def get_team_members(supervisor_id, tenant_id):
    """
    Obtiene los IDs de los miembros del equipo de un supervisor.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT team_member_id 
        FROM Team_Structure 
        WHERE supervisor_id = %s 
        AND tenant_id = %s 
        AND is_active = TRUE
    """, (supervisor_id, tenant_id))
    
    members = cursor.fetchall()
    return [m['team_member_id'] for m in members] + [supervisor_id]
```

**Uso en filtros:**
```python
# En build_user_filter_condition():
if is_supervisor(user_id, tenant_id):
    team = get_team_members(user_id, tenant_id)  # [5, 8, 12]
    return f"{column_name} IN ({','.join(['%s'] * len(team))})", team
```

**Resultado:**
```sql
-- Supervisor ID 5 ve recursos de:
WHERE created_by_user IN (5, 8, 12)  -- Él + su equipo
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### **Endpoints a crear:**
- [ ] GET `/api/teams/my-team`
- [ ] POST `/api/teams/members`
- [ ] DELETE `/api/teams/members/<int:team_member_id>`
- [ ] GET `/api/teams/available-members`
- [ ] GET `/api/teams/all` (opcional - solo admins)

### **Validaciones a implementar:**
- [ ] Verificar que usuario es Supervisor o Admin
- [ ] Verificar que miembro es Reclutador
- [ ] Evitar duplicados
- [ ] Verificar que Supervisor solo gestiona SU equipo
- [ ] Verificar que miembro pertenece al tenant

### **Integraciones:**
- [ ] Usar `is_supervisor()` de `permission_service.py`
- [ ] Usar `is_admin()` de `permission_service.py`
- [ ] Logs de auditoría para cambios en equipos

---

## 🚀 UBICACIÓN EN app.py

Los nuevos endpoints se agregarán después de la sección de usuarios:

```python
# ===============================================================
# SECCIÓN X: GESTIÓN DE EQUIPOS (TEAM_STRUCTURE)
# ===============================================================

@app.route('/api/teams/my-team', methods=['GET'])
@token_required
def get_my_team():
    ...

@app.route('/api/teams/members', methods=['POST'])
@token_required
def add_team_member():
    ...

@app.route('/api/teams/members/<int:team_member_id>', methods=['DELETE'])
@token_required
def remove_team_member(team_member_id):
    ...

@app.route('/api/teams/available-members', methods=['GET'])
@token_required
def get_available_members():
    ...

@app.route('/api/teams/all', methods=['GET'])
@token_required
def get_all_teams():
    ...
```

---

**Tiempo estimado:** 2-3 horas  
**Complejidad:** ALTA (núcleo del sistema de jerarquías)  
**Riesgo:** Medio-Alto (cambios afectan permisos existentes)

**Próximo paso:** Implementar endpoints en `app.py` 🚀

