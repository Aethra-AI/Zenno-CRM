-- =====================================================
-- ARQUITECTURA CORRECTA DE MULTI-TENANCY
-- =====================================================

-- TENANTS = Empresas de reclutamiento (usuarios del sistema)
-- CLIENTES = Empresas que buscan personal (clientes de los tenants)

-- 1. Crear tabla Tenants (empresas de reclutamiento)
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

-- 2. Crear tabla Tenant_Roles (roles específicos por tenant)
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

-- 3. Corregir tabla Users para usar tenant_id correctamente
-- Eliminar id_cliente de Users (solo debe estar en Vacantes)
ALTER TABLE Users DROP COLUMN IF EXISTS id_cliente;

-- Asegurar que Users tenga tenant_id
ALTER TABLE Users ADD COLUMN IF NOT EXISTS tenant_id INT;
ALTER TABLE Users ADD FOREIGN KEY (tenant_id) REFERENCES Tenants(id_tenant);

-- 4. La tabla Clientes se mantiene para empresas que buscan personal
-- (NO se modifica, ya está correcta)

-- 5. Crear índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_users_tenant ON Users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_afiliados_tenant ON Afiliados(tenant_id);
CREATE INDEX IF NOT EXISTS idx_vacantes_tenant ON Vacantes(tenant_id);
CREATE INDEX IF NOT EXISTS idx_postulaciones_tenant ON Postulaciones(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tags_tenant ON Tags(tenant_id);
CREATE INDEX IF NOT EXISTS idx_email_templates_tenant ON Email_Templates(tenant_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_templates_tenant ON Whatsapp_Templates(tenant_id);
