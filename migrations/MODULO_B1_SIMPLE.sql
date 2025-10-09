-- =====================================================
-- 🚀 MÓDULO B1 - Sistema de Permisos
-- Base de datos: whatsapp_backend
-- =====================================================

USE whatsapp_backend;

-- =====================================================
-- 1. ACTUALIZAR TABLA ROLES (agregar Supervisor)
-- =====================================================

-- Agregar rol Supervisor si no existe
INSERT INTO Roles (nombre, descripcion, permisos, activo)
SELECT 'Supervisor', 
       'Gestiona equipos de reclutadores', 
       '{"view_team": true, "manage_team": true, "assign_resources": true}',
       1
WHERE NOT EXISTS (SELECT 1 FROM Roles WHERE nombre = 'Supervisor');

-- Actualizar permisos de Administrador
UPDATE Roles 
SET permisos = '{"all": true, "manage_users": true, "configure_system": true}'
WHERE nombre = 'Administrador';

-- Actualizar permisos de Reclutador
UPDATE Roles 
SET permisos = '{"view_own": true, "create": true, "edit_own": true}'
WHERE nombre = 'Reclutador';


-- =====================================================
-- 2. CREAR TABLA TEAM_STRUCTURE
-- =====================================================

CREATE TABLE IF NOT EXISTS Team_Structure (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    supervisor_id INT NOT NULL,
    team_member_id INT NOT NULL,
    assigned_by INT NOT NULL,
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
-- 3. CREAR TABLA RESOURCE_ASSIGNMENTS
-- =====================================================

CREATE TABLE IF NOT EXISTS Resource_Assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    resource_type ENUM('vacancy', 'client', 'candidate') NOT NULL,
    resource_id INT NOT NULL,
    assigned_to_user INT NOT NULL,
    assigned_by_user INT NOT NULL,
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

-- Ver roles
SELECT id, nombre, descripcion, permisos FROM Roles WHERE activo = 1;

-- Ver tablas creadas
SHOW TABLES LIKE 'Team_Structure';
SHOW TABLES LIKE 'Resource_Assignments';

SELECT '✅ Módulo B1 completado' as resultado;


