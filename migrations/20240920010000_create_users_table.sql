-- Creación de la tabla de roles
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Creación de la tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    role_id INT,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Creación de la tabla de permisos
CREATE TABLE IF NOT EXISTS permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla intermedia para roles y permisos
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla para tokens de restablecimiento de contraseña
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla para el registro de actividad de usuarios
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_action (user_id, action),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insertar roles básicos
INSERT IGNORE INTO roles (id, name, description) VALUES 
(1, 'admin', 'Administrador del sistema con acceso completo'),
(2, 'reclutador', 'Usuario que gestiona candidatos y vacantes'),
(3, 'coordinador', 'Supervisa el proceso de selección'),
(4, 'entrevistador', 'Realiza entrevistas técnicas'),
(5, 'analista', 'Acceso a reportes y análisis');

-- Insertar permisos básicos
INSERT IGNORE INTO permissions (name, description) VALUES
('user_create', 'Crear nuevos usuarios'),
('user_read', 'Ver información de usuarios'),
('user_update', 'Actualizar información de usuarios'),
('user_delete', 'Eliminar usuarios'),
('role_manage', 'Gestionar roles y permisos'),
('candidate_create', 'Crear candidatos'),
('candidate_read', 'Ver información de candidatos'),
('candidate_update', 'Actualizar información de candidatos'),
('candidate_delete', 'Eliminar candidatos'),
('vacancy_manage', 'Gestionar vacantes'),
('interview_manage', 'Gestionar entrevistas'),
('report_view', 'Ver reportes'),
('settings_manage', 'Gestionar configuración del sistema');

-- Asignar todos los permisos al rol de administrador
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT 1, id FROM permissions;

-- Asignar permisos básicos al rol de reclutador
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT 2, id FROM permissions 
WHERE name IN ('candidate_create', 'candidate_read', 'candidate_update', 'vacancy_manage', 'interview_manage');

-- Crear usuario administrador por defecto (contraseña: Admin123!)
-- La contraseña se generará dinámicamente en el código
INSERT IGNORE INTO users (username, email, first_name, last_name, is_active, role_id)
VALUES ('admin', 'admin@henmir.com', 'Administrador', 'del Sistema', TRUE, 1);

-- Crear índice para búsquedas rápidas
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_username ON users(username);
CREATE INDEX idx_user_role ON users(role_id);

-- Crear trigger para actualizar automáticamente las fechas
DELIMITER //
CREATE TRIGGER before_user_update
BEFORE UPDATE ON users
FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END //
DELIMITER ;

-- Crear vista para usuarios con información de roles
CREATE OR REPLACE VIEW vw_users_with_roles AS
SELECT 
    u.id, 
    u.username, 
    u.email, 
    u.first_name, 
    u.last_name, 
    u.phone, 
    u.is_active, 
    u.last_login, 
    u.created_at, 
    u.updated_at,
    r.id as role_id,
    r.name as role_name,
    r.description as role_description
FROM 
    users u
LEFT JOIN 
    roles r ON u.role_id = r.id;
