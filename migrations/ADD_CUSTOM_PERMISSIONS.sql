-- ================================================================
-- 🔐 MIGRACIÓN: Agregar custom_permissions a Users
-- Fecha: Octubre 10, 2025
-- Propósito: Permitir que Admin configure permisos individuales por usuario
-- ================================================================

USE whatsapp_backend;

-- 1. Agregar columna custom_permissions a Users
ALTER TABLE Users 
ADD COLUMN custom_permissions JSON NULL
COMMENT 'Permisos personalizados que sobrescriben los permisos del rol'
AFTER rol_id;

-- 2. Verificar que se agregó correctamente
DESCRIBE Users;

-- 3. Ejemplo de uso:
-- Admin puede dar permisos especiales a un Reclutador específico
-- UPDATE Users 
-- SET custom_permissions = '{
--   "clients": {"create": true, "view_scope": "team"},
--   "dashboard": {"view_financial": true}
-- }'
-- WHERE id = 2;

SELECT 'Migración completada: custom_permissions agregado a Users' as status;

