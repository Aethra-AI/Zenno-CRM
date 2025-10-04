-- =====================================================
-- 🗄️ SCRIPT COMPLETO DE BASE DE DATOS - CRM WHATSAPP
-- =====================================================
-- Este script crea TODAS las tablas necesarias para el backend
-- Basado en el análisis completo del código app.py

-- 1. TABLA TENANTS (Multi-tenant)
CREATE TABLE IF NOT EXISTS Tenants (
    id INT AUTO_INCREMENT PRIMARY KEY,
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

-- 2. TABLA USERS (Usuarios del sistema)
CREATE TABLE IF NOT EXISTS Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    tenant_id INT,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- 3. TABLA USERSESSIONS (Sesiones de usuario)
CREATE TABLE IF NOT EXISTS UserSessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

-- 4. TABLA AFILIADOS (Candidatos)
CREATE TABLE IF NOT EXISTS Afiliados (
    id_afiliado INT AUTO_INCREMENT PRIMARY KEY,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    nombre_completo VARCHAR(255) NOT NULL,
    identidad VARCHAR(20) UNIQUE,
    telefono VARCHAR(20),
    email VARCHAR(255),
    experiencia TEXT,
    ciudad VARCHAR(100),
    grado_academico VARCHAR(100),
    cv_url VARCHAR(500),
    observaciones TEXT,
    contrato_url VARCHAR(500),
    disponibilidad_rotativos BOOLEAN DEFAULT FALSE,
    transporte_propio BOOLEAN DEFAULT FALSE,
    estado VARCHAR(50) DEFAULT 'Activo',
    puntuacion DECIMAL(3,2) DEFAULT 0.00,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    tenant_id INT,
    disponibilidad VARCHAR(100),
    linkedin VARCHAR(255),
    portfolio VARCHAR(255),
    skills TEXT,
    comentarios TEXT,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- 5. TABLA CLIENTES (Empresas que publican vacantes)
CREATE TABLE IF NOT EXISTS Clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    empresa VARCHAR(255) NOT NULL,
    contacto_nombre VARCHAR(255),
    telefono VARCHAR(20),
    email VARCHAR(255),
    sector VARCHAR(100),
    observaciones TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tenant_id INT,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- 6. TABLA VACANTES (Ofertas de trabajo)
CREATE TABLE IF NOT EXISTS Vacantes (
    id_vacante INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    cargo_solicitado VARCHAR(255) NOT NULL,
    descripcion TEXT,
    requisitos TEXT,
    salario_min DECIMAL(10,2),
    salario_max DECIMAL(10,2),
    ciudad VARCHAR(100),
    estado VARCHAR(50) DEFAULT 'Abierta',
    fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre TIMESTAMP,
    tenant_id INT,
    FOREIGN KEY (id_cliente) REFERENCES Clientes(id_cliente) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- 7. TABLA POSTULACIONES (Aplicaciones de candidatos)
CREATE TABLE IF NOT EXISTS Postulaciones (
    id_postulacion INT AUTO_INCREMENT PRIMARY KEY,
    id_afiliado INT NOT NULL,
    id_vacante INT NOT NULL,
    fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(50) DEFAULT 'Recibida',
    comentarios TEXT,
    tenant_id INT,
    FOREIGN KEY (id_afiliado) REFERENCES Afiliados(id_afiliado) ON DELETE CASCADE,
    FOREIGN KEY (id_vacante) REFERENCES Vacantes(id_vacante) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- 8. TABLA ENTREVISTAS (Entrevistas programadas)
CREATE TABLE IF NOT EXISTS Entrevistas (
    id_entrevista INT AUTO_INCREMENT PRIMARY KEY,
    id_postulacion INT NOT NULL,
    fecha_hora TIMESTAMP NOT NULL,
    entrevistador VARCHAR(255),
    resultado VARCHAR(50) DEFAULT 'Programada',
    observaciones TEXT,
    tenant_id INT,
    FOREIGN KEY (id_postulacion) REFERENCES Postulaciones(id_postulacion) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- 9. TABLA CONTRATADOS (Candidatos contratados)
CREATE TABLE IF NOT EXISTS Contratados (
    id_contratacion INT AUTO_INCREMENT PRIMARY KEY,
    id_afiliado INT NOT NULL,
    id_vacante INT NOT NULL,
    fecha_contratacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    salario_final DECIMAL(10,2),
    fecha_inicio TIMESTAMP,
    observaciones TEXT,
    tenant_id INT,
    FOREIGN KEY (id_afiliado) REFERENCES Afiliados(id_afiliado) ON DELETE CASCADE,
    FOREIGN KEY (id_vacante) REFERENCES Vacantes(id_vacante) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- 10. TABLA TAGS (Etiquetas para candidatos)
CREATE TABLE IF NOT EXISTS Tags (
    id_tag INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tag VARCHAR(100) NOT NULL,
    tenant_id INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    UNIQUE KEY unique_tag_tenant (tenant_id, nombre_tag)
);

-- 11. TABLA AFILIADO_TAGS (Relación candidatos-etiquetas)
CREATE TABLE IF NOT EXISTS Afiliado_Tags (
    id_afiliado INT NOT NULL,
    id_tag INT NOT NULL,
    tenant_id INT NOT NULL,
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_afiliado, id_tag, tenant_id),
    FOREIGN KEY (id_afiliado) REFERENCES Afiliados(id_afiliado) ON DELETE CASCADE,
    FOREIGN KEY (id_tag) REFERENCES Tags(id_tag) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- 12. TABLA EMAIL_TEMPLATES (Plantillas de email)
CREATE TABLE IF NOT EXISTS Email_Templates (
    id_template INT AUTO_INCREMENT PRIMARY KEY,
    nombre_plantilla VARCHAR(255) NOT NULL,
    asunto VARCHAR(255),
    cuerpo_html TEXT,
    tenant_id INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- 13. TABLA WHATSAPP_TEMPLATES (Plantillas de WhatsApp)
CREATE TABLE IF NOT EXISTS Whatsapp_Templates (
    id_template INT AUTO_INCREMENT PRIMARY KEY,
    nombre_plantilla VARCHAR(255) NOT NULL,
    cuerpo_mensaje TEXT NOT NULL,
    tenant_id INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- 14. TABLA WHATSAPP_CONFIG (Configuración WhatsApp)
CREATE TABLE IF NOT EXISTS WhatsApp_Config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    config_type VARCHAR(50),
    config_data JSON,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- 15. TABLA PUNTUACIONES_CANDIDATO (Sistema de puntuación)
CREATE TABLE IF NOT EXISTS puntuaciones_candidato (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_afiliado INT NOT NULL,
    puntuacion DECIMAL(3,2) NOT NULL,
    criterios JSON,
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tenant_id INT,
    FOREIGN KEY (id_afiliado) REFERENCES Afiliados(id_afiliado) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- 16. TABLA TENANT_ROLES (Roles específicos por tenant)
CREATE TABLE IF NOT EXISTS Tenant_Roles (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    user_id INT NOT NULL,
    nombre_rol VARCHAR(50) NOT NULL,
    descripcion TEXT,
    permisos JSON,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_tenant_role (user_id, tenant_id)
);

-- =====================================================
-- 📊 INSERTAR DATOS INICIALES
-- =====================================================

-- Insertar tenant por defecto
INSERT IGNORE INTO Tenants (id, nombre_empresa, email_contacto, plan) 
VALUES (1, 'Default Tenant', 'admin@crm.com', 'basic');

-- Insertar usuario admin por defecto
INSERT IGNORE INTO Users (id, email, password_hash, name, tenant_id, role) 
VALUES (1, 'admin@crm.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4Zq8QqQqQq', 'Admin User', 1, 'admin');

-- Insertar rol de admin
INSERT IGNORE INTO Tenant_Roles (tenant_id, user_id, nombre_rol, descripcion, permisos) 
VALUES (1, 1, 'admin', 'Administrador del sistema', '{"all": true}');

-- Insertar plantilla WhatsApp por defecto
INSERT IGNORE INTO Whatsapp_Templates (id_template, nombre_plantilla, cuerpo_mensaje, tenant_id) 
VALUES (1, 'Mensaje por defecto', 'Hola {{nombre}}, hemos recibido tu postulación. Te contactaremos pronto.', 1);

-- =====================================================
-- 🔧 CREAR ÍNDICES PARA RENDIMIENTO
-- =====================================================

-- Índices para Users
CREATE INDEX idx_users_email ON Users(email);
CREATE INDEX idx_users_tenant ON Users(tenant_id);
CREATE INDEX idx_users_active ON Users(is_active);

-- Índices para Afiliados
CREATE INDEX idx_afiliados_tenant ON Afiliados(tenant_id);
CREATE INDEX idx_afiliados_identidad ON Afiliados(identidad);
CREATE INDEX idx_afiliados_email ON Afiliados(email);
CREATE INDEX idx_afiliados_estado ON Afiliados(estado);

-- Índices para Vacantes
CREATE INDEX idx_vacantes_tenant ON Vacantes(tenant_id);
CREATE INDEX idx_vacantes_cliente ON Vacantes(id_cliente);
CREATE INDEX idx_vacantes_estado ON Vacantes(estado);
CREATE INDEX idx_vacantes_ciudad ON Vacantes(ciudad);

-- Índices para Postulaciones
CREATE INDEX idx_postulaciones_tenant ON Postulaciones(tenant_id);
CREATE INDEX idx_postulaciones_afiliado ON Postulaciones(id_afiliado);
CREATE INDEX idx_postulaciones_vacante ON Postulaciones(id_vacante);
CREATE INDEX idx_postulaciones_estado ON Postulaciones(estado);

-- Índices para Entrevistas
CREATE INDEX idx_entrevistas_tenant ON Entrevistas(tenant_id);
CREATE INDEX idx_entrevistas_postulacion ON Entrevistas(id_postulacion);
CREATE INDEX idx_entrevistas_fecha ON Entrevistas(fecha_hora);

-- Índices para Clientes
CREATE INDEX idx_clientes_tenant ON Clientes(tenant_id);
CREATE INDEX idx_clientes_empresa ON Clientes(empresa);

-- Índices para Contratados
CREATE INDEX idx_contratados_tenant ON Contratados(tenant_id);
CREATE INDEX idx_contratados_afiliado ON Contratados(id_afiliado);
CREATE INDEX idx_contratados_vacante ON Contratados(id_vacante);

-- =====================================================
-- ✅ VERIFICACIÓN FINAL
-- =====================================================

-- Mostrar todas las tablas creadas
SHOW TABLES;

-- Mostrar estructura de tablas principales
DESCRIBE Tenants;
DESCRIBE Users;
DESCRIBE Afiliados;
DESCRIBE Vacantes;
DESCRIBE Postulaciones;

-- Verificar datos iniciales
SELECT COUNT(*) as total_tenants FROM Tenants;
SELECT COUNT(*) as total_users FROM Users;
SELECT COUNT(*) as total_templates FROM Whatsapp_Templates;

-- =====================================================
-- 📝 COMENTARIOS FINALES
-- =====================================================

/*
ESQUEMA COMPLETO DE BASE DE DATOS CRM WHATSAPP

Este script crea TODAS las tablas necesarias basándose en el análisis completo del código app.py:

✅ TABLAS PRINCIPALES:
- Tenants (Multi-tenant)
- Users (Usuarios)
- UserSessions (Sesiones)
- Afiliados (Candidatos)
- Clientes (Empresas)
- Vacantes (Ofertas)
- Postulaciones (Aplicaciones)
- Entrevistas (Entrevistas)
- Contratados (Contrataciones)

✅ TABLAS DE GESTIÓN:
- Tags (Etiquetas)
- Afiliado_Tags (Relación candidatos-etiquetas)
- Email_Templates (Plantillas email)
- Whatsapp_Templates (Plantillas WhatsApp)
- WhatsApp_Config (Configuración WhatsApp)
- puntuaciones_candidato (Sistema puntuación)
- Tenant_Roles (Roles por tenant)

✅ CARACTERÍSTICAS:
- Multi-tenancy completo
- Integridad referencial
- Índices optimizados
- Datos iniciales
- Aislamiento por tenant

MANTENIMIENTO:
- Ejecutar este script una sola vez
- Verificar que todas las tablas se crearon correctamente
- El backend debería funcionar sin errores después de esto
*/
