-- Agregar columna para registrar el usuario que creó el candidato
-- Esto permite rastrear quién subió cada CV

ALTER TABLE Afiliados 
ADD COLUMN created_by_user_id INT(11) DEFAULT NULL COMMENT 'ID del usuario que creó/subió el candidato',
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha y hora de creación',
ADD COLUMN updated_by_user_id INT(11) DEFAULT NULL COMMENT 'ID del último usuario que modificó el candidato',
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Fecha y hora de última modificación';

-- Agregar índice para búsquedas por usuario creador
CREATE INDEX idx_afiliados_created_by ON Afiliados(created_by_user_id);
CREATE INDEX idx_afiliados_tenant_created ON Afiliados(tenant_id, created_by_user_id);

-- Agregar foreign key (opcional, comentado por si hay problemas con usuarios eliminados)
-- ALTER TABLE Afiliados 
-- ADD CONSTRAINT fk_afiliados_created_by 
-- FOREIGN KEY (created_by_user_id) REFERENCES Usuarios(id_usuario) ON DELETE SET NULL;

-- Verificar que se agregaron las columnas
DESCRIBE Afiliados;
