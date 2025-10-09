-- ======================================================
-- AGREGAR ROL "SUPERVISOR" Y ACTUALIZAR PERMISOS
-- ======================================================

-- Actualizar rol "Visualizador" a "Supervisor" si existe
UPDATE Roles 
SET nombre = 'Supervisor',
    descripcion = 'Supervisa equipos de reclutadores y gestiona recursos de equipo',
    permisos = JSON_OBJECT(
        'create_candidate', true,
        'edit_candidate', true,
        'delete_candidate', true,
        'view_candidate', true,
        'create_vacancy', true,
        'edit_vacancy', true,
        'delete_vacancy', true,
        'view_vacancy', true,
        'create_client', true,
        'edit_client', true,
        'delete_client', true,
        'view_client', true,
        'create_application', true,
        'edit_application', true,
        'delete_application', true,
        'view_application', true,
        'manage_team', true,
        'view_dashboard', true,
        'view_reports', true
    )
WHERE id = 3 AND nombre = 'Visualizador';

-- Si no existe, insertar el rol Supervisor
INSERT IGNORE INTO Roles (id, nombre, descripcion, permisos, activo, created_at)
VALUES (
    3,
    'Supervisor',
    'Supervisa equipos de reclutadores y gestiona recursos de equipo',
    JSON_OBJECT(
        'create_candidate', true,
        'edit_candidate', true,
        'delete_candidate', true,
        'view_candidate', true,
        'create_vacancy', true,
        'edit_vacancy', true,
        'delete_vacancy', true,
        'view_vacancy', true,
        'create_client', true,
        'edit_client', true,
        'delete_client', true,
        'view_client', true,
        'create_application', true,
        'edit_application', true,
        'delete_application', true,
        'view_application', true,
        'manage_team', true,
        'view_dashboard', true,
        'view_reports', true
    ),
    TRUE,
    NOW()
);

-- Actualizar permisos del Administrador
UPDATE Roles 
SET permisos = JSON_OBJECT(
    'create_candidate', true,
    'edit_candidate', true,
    'delete_candidate', true,
    'view_candidate', true,
    'create_vacancy', true,
    'edit_vacancy', true,
    'delete_vacancy', true,
    'view_vacancy', true,
    'create_client', true,
    'edit_client', true,
    'delete_client', true,
    'view_client', true,
    'create_application', true,
    'edit_application', true,
    'delete_application', true,
    'view_application', true,
    'manage_users', true,
    'manage_team', true,
    'view_dashboard', true,
    'view_reports', true,
    'export_reports', true,
    'manage_roles', true
)
WHERE id = 1 AND nombre = 'Administrador';

-- Actualizar permisos del Reclutador
UPDATE Roles 
SET permisos = JSON_OBJECT(
    'create_candidate', true,
    'edit_candidate', true,
    'delete_candidate', true,
    'view_candidate', true,
    'create_vacancy', true,
    'edit_vacancy', true,
    'delete_vacancy', true,
    'view_vacancy', true,
    'create_client', true,
    'edit_client', true,
    'view_client', true,
    'create_application', true,
    'edit_application', true,
    'view_application', true,
    'view_dashboard', true
)
WHERE id = 2 AND nombre = 'Reclutador';

-- Verificar resultados
SELECT id, nombre, descripcion, activo FROM Roles WHERE activo = TRUE ORDER BY id;

