-- ===============================================================
-- MIGRACIÓN 2: Aumentar tamaño de columna api_key
-- ===============================================================
-- Descripción: La columna api_key es demasiado pequeña (VARCHAR(100))
--              para almacenar las API Keys generadas (64+ caracteres)
-- Fecha: 2025-10-19
-- ===============================================================

-- Aumentar el tamaño de la columna api_key a VARCHAR(255)
ALTER TABLE Public_API_Keys 
MODIFY COLUMN api_key VARCHAR(255) NOT NULL;

-- Verificar el cambio
SELECT 
    COLUMN_NAME,
    COLUMN_TYPE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Public_API_Keys' 
  AND COLUMN_NAME = 'api_key'
  AND TABLE_SCHEMA = DATABASE();
