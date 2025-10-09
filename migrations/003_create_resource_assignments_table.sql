-- =====================================================
-- MÓDULO B1.3: Crear Tabla Resource_Assignments
-- Base de datos: whatsapp_backend
-- Fecha: Octubre 2025
-- =====================================================

-- Verificar base de datos actual
SELECT DATABASE() as 'Base de datos actual';

-- Crear tabla Resource_Assignments
CREATE TABLE IF NOT EXISTS Resource_Assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL COMMENT 'ID del tenant (empresa)',
    resource_type ENUM('vacancy', 'client', 'candidate') NOT NULL COMMENT 'Tipo de recurso',
    resource_id INT NOT NULL COMMENT 'ID del recurso (id_vacante, id_cliente, id_afiliado)',
    assigned_to_user INT NOT NULL COMMENT 'user_id a quien se asigna',
    assigned_by_user INT NOT NULL COMMENT 'user_id quien asignó',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_level ENUM('read', 'write', 'full') DEFAULT 'write' COMMENT 'Nivel de acceso al recurso',
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT COMMENT 'Notas sobre la asignación',
    expires_at TIMESTAMP NULL COMMENT 'Fecha de expiración de asignación (opcional)',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to_user) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by_user) REFERENCES Users(id) ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT unique_resource_assignment UNIQUE (tenant_id, resource_type, resource_id, assigned_to_user)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Asignación de recursos (vacantes, clientes, candidatos) a usuarios';

-- Crear índices para optimizar búsquedas
CREATE INDEX idx_resource_lookup ON Resource_Assignments(resource_type, resource_id, is_active);
CREATE INDEX idx_user_assignments ON Resource_Assignments(assigned_to_user, resource_type, is_active);
CREATE INDEX idx_tenant_assignments ON Resource_Assignments(tenant_id, is_active);
CREATE INDEX idx_assigned_by ON Resource_Assignments(assigned_by_user);
CREATE INDEX idx_user_tenant_type ON Resource_Assignments(assigned_to_user, tenant_id, resource_type, is_active);
CREATE INDEX idx_type_tenant ON Resource_Assignments(resource_type, tenant_id, is_active);

-- Verificar que la tabla se creó correctamente
SHOW CREATE TABLE Resource_Assignments;

-- Verificar índices
SHOW INDEX FROM Resource_Assignments;

-- Verificar ENUMs
SHOW COLUMNS FROM Resource_Assignments WHERE Field IN ('resource_type', 'access_level');

-- Verificar foreign keys
SELECT 
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_NAME = 'Resource_Assignments'
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
AND TABLE_NAME = 'Resource_Assignments';

SELECT '✅ Tabla Resource_Assignments creada exitosamente' as resultado;


