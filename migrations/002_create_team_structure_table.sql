-- =====================================================
-- MÓDULO B1.2: Crear Tabla Team_Structure
-- Base de datos: whatsapp_backend
-- Fecha: Octubre 2025
-- =====================================================

-- Verificar base de datos actual
SELECT DATABASE() as 'Base de datos actual';

-- Crear tabla Team_Structure
CREATE TABLE IF NOT EXISTS Team_Structure (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL COMMENT 'ID del tenant (empresa)',
    supervisor_id INT NOT NULL COMMENT 'user_id del supervisor',
    team_member_id INT NOT NULL COMMENT 'user_id del reclutador',
    assigned_by INT NOT NULL COMMENT 'user_id del admin que asignó',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT COMMENT 'Notas sobre la asignación',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (supervisor_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (team_member_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES Users(id) ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT unique_team_assignment UNIQUE (tenant_id, supervisor_id, team_member_id),
    
    -- Verificar que supervisor y team_member sean diferentes
    CONSTRAINT check_different_users CHECK (supervisor_id != team_member_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Jerarquía de equipos: supervisores y sus reclutadores';

-- Crear índices para optimizar búsquedas
CREATE INDEX idx_supervisor ON Team_Structure(supervisor_id, is_active);
CREATE INDEX idx_team_member ON Team_Structure(team_member_id, is_active);
CREATE INDEX idx_tenant_active ON Team_Structure(tenant_id, is_active);
CREATE INDEX idx_supervisor_tenant ON Team_Structure(supervisor_id, tenant_id, is_active);

-- Verificar que la tabla se creó correctamente
SHOW CREATE TABLE Team_Structure;

-- Verificar índices
SHOW INDEX FROM Team_Structure;

-- Verificar foreign keys
SELECT 
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_NAME = 'Team_Structure'
AND CONSTRAINT_SCHEMA = DATABASE()
AND REFERENCED_TABLE_NAME IS NOT NULL;

-- Verificación final
SELECT 
    TABLE_NAME,
    ENGINE,
    TABLE_COLLATION,
    TABLE_COMMENT
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'Team_Structure';

SELECT '✅ Tabla Team_Structure creada exitosamente' as resultado;


