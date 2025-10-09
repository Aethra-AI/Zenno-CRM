-- =====================================================
-- 🔍 VERIFICACIÓN COMPLETA - MÓDULO B1
-- Base de datos: whatsapp_backend
-- =====================================================

USE whatsapp_backend;

-- =====================================================
-- 1. VERIFICAR ROLES (debe mostrar 4 roles con permisos JSON)
-- =====================================================

SELECT 
    id, 
    nombre, 
    descripcion, 
    permisos,
    activo
FROM Roles 
WHERE activo = 1
ORDER BY id;

-- Debe mostrar:
-- 1 | Administrador | ... | {"all": true, "manage_users": true, "configure_system": true}
-- 2 | Reclutador    | ... | {"view_own": true, "create": true, "edit_own": true}
-- 3 | Usuario       | ... | {"view": true}
-- 4 | Supervisor    | ... | {"view_team": true, "manage_team": true, "assign_resources": true}


-- =====================================================
-- 2. VERIFICAR QUE TABLA TEAM_STRUCTURE EXISTE
-- =====================================================

SHOW TABLES LIKE 'Team_Structure';

-- Debe mostrar: Team_Structure


-- =====================================================
-- 3. VERIFICAR ESTRUCTURA DE TEAM_STRUCTURE
-- =====================================================

DESCRIBE Team_Structure;

-- Debe mostrar columnas:
-- id, tenant_id, supervisor_id, team_member_id, assigned_by (NULL permitido), 
-- assigned_at, is_active


-- =====================================================
-- 4. VERIFICAR FOREIGN KEYS DE TEAM_STRUCTURE
-- =====================================================

SELECT 
    CONSTRAINT_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'whatsapp_backend'
  AND TABLE_NAME = 'Team_Structure'
  AND REFERENCED_TABLE_NAME IS NOT NULL;

-- Debe mostrar 4 foreign keys hacia: Tenants(id), Users(id) x3


-- =====================================================
-- 5. VERIFICAR QUE TABLA RESOURCE_ASSIGNMENTS EXISTE
-- =====================================================

SHOW TABLES LIKE 'Resource_Assignments';

-- Debe mostrar: Resource_Assignments


-- =====================================================
-- 6. VERIFICAR ESTRUCTURA DE RESOURCE_ASSIGNMENTS
-- =====================================================

DESCRIBE Resource_Assignments;

-- Debe mostrar columnas:
-- id, tenant_id, resource_type (ENUM), resource_id, assigned_to_user, 
-- assigned_by_user (NULL permitido), assigned_at, access_level (ENUM), is_active


-- =====================================================
-- 7. VERIFICAR FOREIGN KEYS DE RESOURCE_ASSIGNMENTS
-- =====================================================

SELECT 
    CONSTRAINT_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'whatsapp_backend'
  AND TABLE_NAME = 'Resource_Assignments'
  AND REFERENCED_TABLE_NAME IS NOT NULL;

-- Debe mostrar 3 foreign keys hacia: Tenants(id), Users(id) x2


-- =====================================================
-- 8. VERIFICAR ÍNDICES DE TEAM_STRUCTURE
-- =====================================================

SHOW INDEX FROM Team_Structure;

-- Debe mostrar índices en:
-- - tenant_id, supervisor_id, team_member_id (UNIQUE)
-- - supervisor_id + is_active
-- - team_member_id + is_active


-- =====================================================
-- 9. VERIFICAR ÍNDICES DE RESOURCE_ASSIGNMENTS
-- =====================================================

SHOW INDEX FROM Resource_Assignments;

-- Debe mostrar índices en:
-- - tenant_id, resource_type, resource_id, assigned_to_user (UNIQUE)
-- - resource_type + resource_id + is_active
-- - assigned_to_user + is_active


-- =====================================================
-- 10. VERIFICAR ENUM DE RESOURCE_TYPE
-- =====================================================

SELECT COLUMN_TYPE 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'whatsapp_backend' 
  AND TABLE_NAME = 'Resource_Assignments' 
  AND COLUMN_NAME = 'resource_type';

-- Debe mostrar: enum('vacancy','client','candidate')


-- =====================================================
-- 11. VERIFICAR ENUM DE ACCESS_LEVEL
-- =====================================================

SELECT COLUMN_TYPE 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'whatsapp_backend' 
  AND TABLE_NAME = 'Resource_Assignments' 
  AND COLUMN_NAME = 'access_level';

-- Debe mostrar: enum('read','write','full')


-- =====================================================
-- 12. RESUMEN GENERAL
-- =====================================================

SELECT 
    'Roles actualizados' as verificacion,
    COUNT(*) as cantidad,
    'Debe ser 4' as esperado
FROM Roles WHERE activo = 1

UNION ALL

SELECT 
    'Team_Structure creada' as verificacion,
    COUNT(*) as cantidad,
    'Debe ser 1' as esperado
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'whatsapp_backend' 
  AND TABLE_NAME = 'Team_Structure'

UNION ALL

SELECT 
    'Resource_Assignments creada' as verificacion,
    COUNT(*) as cantidad,
    'Debe ser 1' as esperado
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'whatsapp_backend' 
  AND TABLE_NAME = 'Resource_Assignments'

UNION ALL

SELECT 
    'Foreign keys Team_Structure' as verificacion,
    COUNT(*) as cantidad,
    'Debe ser 4' as esperado
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'whatsapp_backend'
  AND TABLE_NAME = 'Team_Structure'
  AND REFERENCED_TABLE_NAME IS NOT NULL

UNION ALL

SELECT 
    'Foreign keys Resource_Assignments' as verificacion,
    COUNT(*) as cantidad,
    'Debe ser 3' as esperado
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'whatsapp_backend'
  AND TABLE_NAME = 'Resource_Assignments'
  AND REFERENCED_TABLE_NAME IS NOT NULL;


-- =====================================================
-- ✅ FIN DE LA VERIFICACIÓN
-- =====================================================

SELECT '✅ Verificación completada - Revisa los resultados arriba' as resultado;


