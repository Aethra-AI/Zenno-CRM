-- Crear tabla de Tenants para gestión multi-empresa
CREATE TABLE IF NOT EXISTS Tenants (
    id_tenant INT AUTO_INCREMENT PRIMARY KEY,
    nombre_empresa VARCHAR(100) NOT NULL,
    email_contacto VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    direccion TEXT,
    plan VARCHAR(20) DEFAULT 'basic' CHECK (plan IN ('basic', 'premium', 'enterprise')),
    api_key VARCHAR(255) UNIQUE,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Crear tabla de roles específicos para tenants
CREATE TABLE IF NOT EXISTS Tenant_Roles (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    nombre_rol VARCHAR(50) NOT NULL,
    descripcion TEXT,
    permisos JSON,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id_tenant) ON DELETE CASCADE,
    UNIQUE KEY unique_rol_tenant (tenant_id, nombre_rol)
);

-- Agregar columna tenant_id a Users si no existe
ALTER TABLE Users ADD COLUMN IF NOT EXISTS tenant_id INT;
ALTER TABLE Users ADD FOREIGN KEY (tenant_id) REFERENCES Tenants(id_tenant);

-- Crear índices para mejor rendimiento
CREATE INDEX idx_users_tenant ON Users(tenant_id);
CREATE INDEX idx_afiliados_tenant ON Afiliados(tenant_id);
CREATE INDEX idx_vacantes_tenant ON Vacantes(tenant_id);
CREATE INDEX idx_postulaciones_tenant ON Postulaciones(tenant_id);
