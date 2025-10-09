-- =====================================================
-- 🚀 SCRIPT MAESTRO: EJECUTAR MÓDULO B1 COMPLETO
-- =====================================================
-- Este script ejecuta los 3 scripts del Módulo B1 en orden
-- Base de datos: whatsapp_backend
-- Fecha: Octubre 2025
-- =====================================================

-- PASO 0: Verificar base de datos
USE whatsapp_backend;
SELECT DATABASE() as 'Base de datos actual', NOW() as 'Fecha y hora';

-- =====================================================
-- PASO 1: Actualizar Roles (B1.1)
-- =====================================================
SELECT '🔧 PASO 1: Actualizando tabla Roles...' as mensaje;

-- Agregar rol Supervisor
INSERT INTO Roles (nombre, descripcion, permisos, activo)
SELECT 'Supervisor', 
       'Gestiona equipos de reclutadores y sus recursos', 
       JSON_OBJECT(
           'view_candidates', true,
           'view_own_candidates', true,
           'view_team_candidates', true,
           'create_candidate', true,
           'edit_own_candidates', true,
           'edit_team_candidates', true,
           'delete_team_candidates', false,
           'view_applications', true,
           'view_own_applications', true,
           'view_team_applications', true,
           'create_application', true,
           'edit_own_applications', true,
           'edit_team_applications', true,
           'view_interviews', true,
           'view_own_interviews', true,
           'view_team_interviews', true,
           'create_interview', true,
           'edit_own_interviews', true,
           'edit_team_interviews', true,
           'view_vacancies', true,
           'view_assigned_vacancies', true,
           'create_vacancy', true,
           'edit_own_vacancies', true,
           'view_clients', true,
           'view_assigned_clients', true,
           'create_client', false,
           'edit_assigned_clients', true,
           'view_hired', true,
           'view_own_hired', true,
           'view_team_hired', true,
           'create_hired', true,
           'view_team_reports', true,
           'assign_resources_to_team', true,
           'manage_team_members', false
       ),
       true
WHERE NOT EXISTS (SELECT 1 FROM Roles WHERE nombre = 'Supervisor');

-- Actualizar permisos Administrador
UPDATE Roles 
SET permisos = JSON_OBJECT(
    'view_all_data', true,
    'view_candidates', true,
    'create_candidate', true,
    'edit_any_candidate', true,
    'delete_any_candidate', true,
    'view_applications', true,
    'create_application', true,
    'edit_any_application', true,
    'delete_any_application', true,
    'view_interviews', true,
    'create_interview', true,
    'edit_any_interview', true,
    'delete_any_interview', true,
    'view_vacancies', true,
    'create_vacancy', true,
    'edit_any_vacancy', true,
    'delete_any_vacancy', true,
    'view_clients', true,
    'create_client', true,
    'edit_any_client', true,
    'delete_any_client', true,
    'view_hired', true,
    'create_hired', true,
    'edit_any_hired', true,
    'delete_any_hired', true,
    'manage_users', true,
    'manage_roles', true,
    'manage_teams', true,
    'assign_any_resource', true,
    'view_all_reports', true,
    'configure_system', true,
    'manage_integrations', true,
    'manage_whatsapp', true
),
descripcion = 'Acceso completo al sistema - Gestiona usuarios, equipos y configuración'
WHERE nombre = 'Administrador';

-- Actualizar permisos Reclutador
UPDATE Roles 
SET permisos = JSON_OBJECT(
    'view_own_candidates', true,
    'view_assigned_candidates', true,
    'create_candidate', true,
    'edit_own_candidates', true,
    'edit_assigned_candidates', true,
    'delete_own_candidates', false,
    'view_own_applications', true,
    'view_assigned_applications', true,
    'create_application', true,
    'edit_own_applications', true,
    'edit_assigned_applications', true,
    'view_own_interviews', true,
    'view_assigned_interviews', true,
    'create_interview', true,
    'edit_own_interviews', true,
    'edit_assigned_interviews', true,
    'view_assigned_vacancies', true,
    'create_application_for_assigned_vacancy', true,
    'view_assigned_clients', true,
    'view_own_hired', true,
    'view_assigned_hired', true,
    'create_hired', true,
    'view_own_reports', true
),
descripcion = 'Gestión de candidatos y vacantes asignadas - Acceso limitado a recursos propios'
WHERE nombre = 'Reclutador';

SELECT '✅ PASO 1 COMPLETADO: Roles actualizados' as resultado;

-- =====================================================
-- PASO 2: Crear Team_Structure (B1.2)
-- =====================================================
SELECT '🔧 PASO 2: Creando tabla Team_Structure...' as mensaje;

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
    
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (supervisor_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (team_member_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES Users(id) ON DELETE SET NULL,
    
    CONSTRAINT unique_team_assignment UNIQUE (tenant_id, supervisor_id, team_member_id),
    CONSTRAINT check_different_users CHECK (supervisor_id != team_member_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Jerarquía de equipos: supervisores y sus reclutadores';

CREATE INDEX idx_supervisor ON Team_Structure(supervisor_id, is_active);
CREATE INDEX idx_team_member ON Team_Structure(team_member_id, is_active);
CREATE INDEX idx_tenant_active ON Team_Structure(tenant_id, is_active);
CREATE INDEX idx_supervisor_tenant ON Team_Structure(supervisor_id, tenant_id, is_active);

SELECT '✅ PASO 2 COMPLETADO: Tabla Team_Structure creada' as resultado;

-- =====================================================
-- PASO 3: Crear Resource_Assignments (B1.3)
-- =====================================================
SELECT '🔧 PASO 3: Creando tabla Resource_Assignments...' as mensaje;

CREATE TABLE IF NOT EXISTS Resource_Assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL COMMENT 'ID del tenant (empresa)',
    resource_type ENUM('vacancy', 'client', 'candidate') NOT NULL COMMENT 'Tipo de recurso',
    resource_id INT NOT NULL COMMENT 'ID del recurso (id_vacante, id_cliente, id_afiliado)',
    assigned_to_user INT NOT NULL COMMENT 'user_id a quien se asigna',
    assigned_by_user INT NOT NULL COMMENT 'user_id quien asignó',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_level ENUM('read', 'write', 'full') DEFAULT 'write' COMMENT 'Nivel de acceso',
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT COMMENT 'Notas sobre la asignación',
    expires_at TIMESTAMP NULL COMMENT 'Fecha de expiración (opcional)',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to_user) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by_user) REFERENCES Users(id) ON DELETE SET NULL,
    
    CONSTRAINT unique_resource_assignment UNIQUE (tenant_id, resource_type, resource_id, assigned_to_user)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Asignación de recursos (vacantes, clientes, candidatos) a usuarios';

CREATE INDEX idx_resource_lookup ON Resource_Assignments(resource_type, resource_id, is_active);
CREATE INDEX idx_user_assignments ON Resource_Assignments(assigned_to_user, resource_type, is_active);
CREATE INDEX idx_tenant_assignments ON Resource_Assignments(tenant_id, is_active);
CREATE INDEX idx_assigned_by ON Resource_Assignments(assigned_by_user);
CREATE INDEX idx_user_tenant_type ON Resource_Assignments(assigned_to_user, tenant_id, resource_type, is_active);
CREATE INDEX idx_type_tenant ON Resource_Assignments(resource_type, tenant_id, is_active);

SELECT '✅ PASO 3 COMPLETADO: Tabla Resource_Assignments creada' as resultado;

-- =====================================================
-- VERIFICACIÓN FINAL
-- =====================================================
SELECT '🔍 VERIFICACIÓN FINAL...' as mensaje;

-- Verificar Roles
SELECT 
    '✅ Roles' as tabla,
    (SELECT COUNT(*) FROM Roles WHERE activo = 1) as total_roles,
    (SELECT COUNT(*) FROM Roles WHERE nombre = 'Supervisor' AND activo = 1) as tiene_supervisor,
    (SELECT COUNT(*) FROM Roles WHERE permisos IS NOT NULL AND activo = 1) as roles_con_permisos;

-- Verificar Team_Structure
SELECT 
    '✅ Team_Structure' as tabla,
    COUNT(*) as total_registros
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'Team_Structure';

-- Verificar Resource_Assignments
SELECT 
    '✅ Resource_Assignments' as tabla,
    COUNT(*) as total_registros
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'Resource_Assignments';

-- Mostrar resumen de Roles
SELECT 
    id,
    nombre,
    descripcion,
    JSON_LENGTH(permisos) as cantidad_permisos,
    activo
FROM Roles
WHERE activo = 1
ORDER BY id;

-- =====================================================
-- RESULTADO FINAL
-- =====================================================
SELECT '
╔═══════════════════════════════════════════════════════╗
║     🎉 MÓDULO B1 EJECUTADO EXITOSAMENTE 🎉          ║
╚═══════════════════════════════════════════════════════╝

✅ Tabla Roles actualizada con 3 roles
✅ Rol Supervisor agregado
✅ Permisos JSON definidos para todos los roles
✅ Tabla Team_Structure creada con índices
✅ Tabla Resource_Assignments creada con índices

📊 Estado final:
   • 3 roles activos (Admin, Supervisor, Reclutador)
   • 2 tablas nuevas creadas
   • Sistema de permisos listo

🚀 Próximo paso: Módulo B2 (Modificar tablas existentes)
' as RESULTADO;


