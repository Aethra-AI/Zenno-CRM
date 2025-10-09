-- =====================================================
-- ⚠️  ROLLBACK COMPLETO DEL MÓDULO B1
-- =====================================================
-- ADVERTENCIA: Este script deshace TODOS los cambios del módulo B1
-- Ejecutar solo si es necesario revertir completamente
-- Base de datos: whatsapp_backend
-- =====================================================

USE whatsapp_backend;
SELECT DATABASE() as 'Base de datos actual', NOW() as 'Fecha y hora';

SELECT '⚠️  INICIANDO ROLLBACK DEL MÓDULO B1...' as mensaje;

-- Paso 1: Eliminar tablas nuevas (en orden inverso de dependencias)
SELECT '🗑️  Eliminando Resource_Assignments...' as mensaje;
DROP TABLE IF EXISTS Resource_Assignments;

SELECT '🗑️  Eliminando Team_Structure...' as mensaje;
DROP TABLE IF EXISTS Team_Structure;

-- Paso 2: Revertir cambios en Roles
SELECT '🔄 Revirtiendo cambios en tabla Roles...' as mensaje;

-- Eliminar rol Supervisor
DELETE FROM Roles WHERE nombre = 'Supervisor';

-- Limpiar permisos (opcional - depende si quieres mantener permisos de Admin y Reclutador)
-- UPDATE Roles SET permisos = NULL WHERE nombre IN ('Administrador', 'Reclutador');

-- Paso 3: Verificar que todo se revirtió
SELECT '🔍 Verificando rollback...' as mensaje;

SELECT 
    (SELECT COUNT(*) FROM Roles WHERE nombre = 'Supervisor') as supervisores_quedan,
    (SELECT COUNT(*) FROM information_schema.TABLES 
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'Team_Structure') as tabla_team_existe,
    (SELECT COUNT(*) FROM information_schema.TABLES 
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'Resource_Assignments') as tabla_resources_existe;

-- Verificar estado de Roles
SELECT 
    id,
    nombre,
    descripcion,
    JSON_LENGTH(permisos) as cantidad_permisos,
    activo
FROM Roles
WHERE activo = 1
ORDER BY id;

SELECT '
╔═══════════════════════════════════════════════════════╗
║     ✅ ROLLBACK COMPLETADO                           ║
╚═══════════════════════════════════════════════════════╝

Si todos los valores son 0, el rollback fue exitoso:
- supervisores_quedan: 0
- tabla_team_existe: 0
- tabla_resources_existe: 0

🔄 La base de datos ha sido revertida al estado anterior al Módulo B1
' as RESULTADO;


