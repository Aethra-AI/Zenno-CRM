-- ================================================================
-- 🔐 ACTUALIZACIÓN: Permisos granulares en Roles
-- Fecha: Octubre 10, 2025
-- Propósito: Definir estructura completa de permisos por rol
-- ================================================================

USE whatsapp_backend;

-- Actualizar permisos del rol Administrador (Control Total)
UPDATE Roles 
SET permisos = '{
  "all": true,
  "candidates": {"view_scope": "all", "create": true, "edit_scope": "all", "delete_scope": "all", "upload_excel": true, "export": true},
  "vacancies": {"view_scope": "all", "create": true, "edit_scope": "all", "delete_scope": "all", "close": true},
  "clients": {"view_scope": "all", "create": true, "edit_scope": "all", "delete_scope": "all", "view_financial": true},
  "applications": {"view_scope": "all", "create": true, "edit_scope": "all", "delete_scope": "all"},
  "interviews": {"view_scope": "all", "create": true, "edit_scope": "all", "delete_scope": "all"},
  "hired": {"view_scope": "all", "create": true, "register_payment": true, "delete": true},
  "dashboard": {"view_scope": "all", "view_financial": true},
  "reports": {"view_scope": "all", "export": true},
  "users": {"view_scope": "all", "create": true, "edit_scope": "all", "delete": true, "assign_resources": true},
  "teams": {"manage": true},
  "roles": {"view": true, "edit": true},
  "permissions": {"view": true, "edit": true},
  "tags": {"create": true, "edit": true, "delete": true},
  "templates": {"create": true, "edit": true, "delete": true},
  "whatsapp": {"view_conversations": true, "send_messages": true, "manage_config": true, "manage_templates": true}
}'
WHERE nombre = 'Administrador';

-- Actualizar permisos del rol Supervisor (Gestión de Equipo)
UPDATE Roles 
SET permisos = '{
  "candidates": {"view_scope": "team", "create": true, "edit_scope": "team", "delete_scope": "team", "upload_excel": false, "export": true},
  "vacancies": {"view_scope": "team", "create": true, "edit_scope": "team", "delete_scope": "none", "close": true},
  "clients": {"view_scope": "team", "create": true, "edit_scope": "team", "delete_scope": "none", "view_financial": false},
  "applications": {"view_scope": "team", "create": true, "edit_scope": "team", "delete_scope": "none"},
  "interviews": {"view_scope": "team", "create": true, "edit_scope": "team", "delete_scope": "none"},
  "hired": {"view_scope": "team", "create": true, "register_payment": false, "delete": false},
  "dashboard": {"view_scope": "team", "view_financial": false},
  "reports": {"view_scope": "team", "export": true},
  "users": {"view_scope": "team", "create": false, "edit_scope": "self", "delete": false, "assign_resources": true},
  "teams": {"manage": true},
  "roles": {"view": true, "edit": false},
  "permissions": {"view": false, "edit": false},
  "tags": {"create": true, "edit": true, "delete": false},
  "templates": {"create": true, "edit": true, "delete": false},
  "whatsapp": {"view_conversations": true, "send_messages": true, "manage_config": false, "manage_templates": true}
}'
WHERE nombre = 'Supervisor';

-- Actualizar permisos del rol Reclutador (Solo Propios)
UPDATE Roles 
SET permisos = '{
  "candidates": {"view_scope": "own", "create": true, "edit_scope": "own", "delete_scope": "none", "upload_excel": false, "export": false},
  "vacancies": {"view_scope": "own", "create": true, "edit_scope": "own", "delete_scope": "none", "close": true},
  "clients": {"view_scope": "own", "create": false, "edit_scope": "none", "delete_scope": "none", "view_financial": false},
  "applications": {"view_scope": "own", "create": true, "edit_scope": "own", "delete_scope": "none"},
  "interviews": {"view_scope": "own", "create": true, "edit_scope": "own", "delete_scope": "none"},
  "hired": {"view_scope": "own", "create": true, "register_payment": false, "delete": false},
  "dashboard": {"view_scope": "own", "view_financial": false},
  "reports": {"view_scope": "own", "export": false},
  "users": {"view_scope": "self", "create": false, "edit_scope": "self", "delete": false, "assign_resources": false},
  "teams": {"manage": false},
  "roles": {"view": false, "edit": false},
  "permissions": {"view": false, "edit": false},
  "tags": {"create": false, "edit": false, "delete": false},
  "templates": {"create": false, "edit": false, "delete": false},
  "whatsapp": {"view_conversations": false, "send_messages": false, "manage_config": false, "manage_templates": false}
}'
WHERE nombre = 'Reclutador';

-- Verificar que se actualizaron correctamente
SELECT id, nombre, JSON_PRETTY(permisos) as permisos_formato 
FROM Roles 
WHERE nombre IN ('Administrador', 'Supervisor', 'Reclutador');

SELECT 'Permisos actualizados correctamente en Roles' as status;

