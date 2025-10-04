-- Agregar columna tenant_id a la tabla Afiliados
ALTER TABLE Afiliados ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id_afiliado;

-- Agregar índice para mejor rendimiento
ALTER TABLE Afiliados ADD INDEX idx_tenant_id (tenant_id);

-- Actualizar registros existentes (asumiendo que pertenecen al tenant 1)
UPDATE Afiliados SET tenant_id = 1 WHERE tenant_id IS NULL OR tenant_id = 0;
