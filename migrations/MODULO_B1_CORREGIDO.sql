-- =====================================================
-- 🚀 MÓDULO B1 - Sistema de Permisos (CORREGIDO)
-- Base de datos: whatsapp_backend
-- =====================================================

USE whatsapp_backend;

-- Ya se ejecutó exitosamente la parte de Roles
-- Solo ejecutar la creación de tablas con el fix:

-- =====================================================
-- 2. CREAR TABLA TEAM_STRUCTURE (CORREGIDO)
-- =====================================================

CREATE TABLE IF NOT EXISTS Team_Structure (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    supervisor_id INT NOT NULL,
    team_member_id INT NOT NULL,
    assigned_by INT NULL,  -- ← CAMBIADO A NULL (porque tiene ON DELETE SET NULL)
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (supervisor_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (team_member_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES Users(id) ON DELETE SET NULL,
    
    UNIQUE KEY (tenant_id, supervisor_id, team_member_id),
    INDEX (supervisor_id, is_active),
    INDEX (team_member_id, is_active)
) ENGINE=InnoDB;


-- =====================================================
-- 3. CREAR TABLA RESOURCE_ASSIGNMENTS (CORREGIDO)
-- =====================================================

CREATE TABLE IF NOT EXISTS Resource_Assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    resource_type ENUM('vacancy', 'client', 'candidate') NOT NULL,
    resource_id INT NOT NULL,
    assigned_to_user INT NOT NULL,
    assigned_by_user INT NULL,  -- ← CAMBIADO A NULL (porque tiene ON DELETE SET NULL)
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_level ENUM('read', 'write', 'full') DEFAULT 'write',
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to_user) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by_user) REFERENCES Users(id) ON DELETE SET NULL,
    
    UNIQUE KEY (tenant_id, resource_type, resource_id, assigned_to_user),
    INDEX (resource_type, resource_id, is_active),
    INDEX (assigned_to_user, is_active)
) ENGINE=InnoDB;


-- =====================================================
-- ✅ VERIFICACIÓN
-- =====================================================

SELECT id, nombre, permisos FROM Roles WHERE activo = 1;

SHOW TABLES LIKE 'Team_Structure';
SHOW TABLES LIKE 'Resource_Assignments';

DESCRIBE Team_Structure;
DESCRIBE Resource_Assignments;

SELECT '✅ Módulo B1 completado correctamente' as resultado;


