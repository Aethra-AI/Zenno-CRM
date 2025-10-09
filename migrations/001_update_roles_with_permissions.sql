-- =====================================================
-- MÓDULO B1.1: Actualizar Roles con Sistema de Permisos
-- Base de datos: whatsapp_backend
-- Fecha: Octubre 2025
-- =====================================================

-- Verificar base de datos actual
SELECT DATABASE() as 'Base de datos actual';

-- 1. Agregar rol "Supervisor" si no existe
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

-- 2. Actualizar permisos del Administrador
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

-- 3. Actualizar permisos del Reclutador
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

-- 4. Verificar que los 3 roles existen y tienen permisos
SELECT 
    id,
    nombre,
    descripcion,
    activo,
    JSON_LENGTH(permisos) as cantidad_permisos,
    created_at
FROM Roles
WHERE activo = 1
ORDER BY id;

-- 5. Mostrar permisos de cada rol (formato legible)
SELECT 
    nombre,
    JSON_PRETTY(permisos) as permisos_detallados
FROM Roles 
WHERE activo = 1
ORDER BY id;

-- 6. Verificación final
SELECT 
    (SELECT COUNT(*) FROM Roles WHERE activo = 1) as total_roles,
    (SELECT COUNT(*) FROM Roles WHERE nombre = 'Supervisor' AND activo = 1) as tiene_supervisor,
    (SELECT COUNT(*) FROM Roles WHERE permisos IS NOT NULL AND activo = 1) as roles_con_permisos
FROM dual;

-- Resultado esperado:
-- total_roles: 3
-- tiene_supervisor: 1
-- roles_con_permisos: 3


