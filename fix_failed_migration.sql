-- ===============================================================
-- SCRIPT PARA LIMPIAR MIGRACIÓN FALLIDA
-- ===============================================================
-- Este script elimina la migración fallida para que pueda
-- ejecutarse nuevamente con la corrección.
-- ===============================================================

-- 1. Eliminar el registro de la migración fallida
DELETE FROM Database_Migrations WHERE id = 1;

-- 2. Eliminar tablas parcialmente creadas (si existen)
DROP TABLE IF EXISTS API_Key_Rate_Limits;
DROP TABLE IF EXISTS API_Key_Logs;
DROP TABLE IF EXISTS Tenant_API_Keys;
DROP TABLE IF EXISTS API_Endpoints_Disponibles;

-- 3. Eliminar procedimientos almacenados (si existen)
DROP PROCEDURE IF EXISTS cleanup_api_logs;
DROP PROCEDURE IF EXISTS get_api_key_stats;

-- 4. Verificar que todo se limpió
SELECT 'Limpieza completada. Reinicia el servidor para ejecutar la migración corregida.' as status;
