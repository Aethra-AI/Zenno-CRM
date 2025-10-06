-- Limpieza simple de la tabla Afiliados
-- Eliminar columnas redundantes y reorganizar estructura

-- 1. Eliminar columnas innecesarias
ALTER TABLE Afiliados 
DROP COLUMN IF EXISTS contrato_url,
DROP COLUMN IF EXISTS disponibilidad,
DROP COLUMN IF EXISTS comentarios,
DROP COLUMN IF EXISTS habilidades,
DROP COLUMN IF EXISTS nacionalidad;

-- 2. Renombrar columnas para consistencia (opcional)
-- ALTER TABLE Afiliados CHANGE disponibilidad_rotativos disponibilidad_rotativos ENUM('si', 'no', 'parcial') DEFAULT 'no';
-- ALTER TABLE Afiliados CHANGE transporte_propio transporte_propio ENUM('si', 'no') DEFAULT 'no';

-- 3. Agregar índices para optimización (opcional)
-- ALTER TABLE Afiliados ADD INDEX idx_estado (estado);
-- ALTER TABLE Afiliados ADD INDEX idx_ciudad (ciudad);
-- ALTER TABLE Afiliados ADD INDEX idx_fecha_registro (fecha_registro);

-- 4. Verificar estructura final
-- DESCRIBE Afiliados;
