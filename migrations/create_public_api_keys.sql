-- ===============================================================
-- SISTEMA DE API KEYS PÚBLICAS PARA MULTI-TENANT
-- ===============================================================
-- Este script crea la infraestructura necesaria para que cada
-- tenant pueda tener sus propias API Keys para compartir datos
-- de forma segura con aplicaciones externas.
-- ===============================================================

-- Tabla principal de API Keys por tenant
CREATE TABLE IF NOT EXISTS Tenant_API_Keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    
    -- Identificadores de la API Key
    api_key VARCHAR(64) NOT NULL UNIQUE COMMENT 'Clave pública (ej: hnm_live_abc123...)',
    api_secret_hash VARCHAR(255) NOT NULL COMMENT 'Hash del secreto (bcrypt)',
    
    -- Información descriptiva
    nombre_descriptivo VARCHAR(255) DEFAULT NULL COMMENT 'Nombre para identificar el uso de esta key',
    descripcion TEXT DEFAULT NULL COMMENT 'Descripción del propósito de esta API key',
    
    -- Control de estado
    activa BOOLEAN DEFAULT TRUE COMMENT 'Si la key está activa o desactivada',
    
    -- Fechas de control
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion DATETIME DEFAULT NULL COMMENT 'Fecha de expiración (NULL = sin expiración)',
    ultimo_uso DATETIME DEFAULT NULL COMMENT 'Última vez que se usó esta key',
    
    -- Estadísticas de uso
    total_requests INT DEFAULT 0 COMMENT 'Total de peticiones realizadas con esta key',
    requests_exitosos INT DEFAULT 0 COMMENT 'Peticiones exitosas',
    requests_fallidos INT DEFAULT 0 COMMENT 'Peticiones fallidas',
    
    -- Límites y restricciones
    rate_limit_per_minute INT DEFAULT 100 COMMENT 'Máximo de requests por minuto',
    rate_limit_per_day INT DEFAULT 10000 COMMENT 'Máximo de requests por día',
    
    -- Permisos específicos
    permisos JSON DEFAULT NULL COMMENT 'Permisos específicos: {"vacancies": true, "candidates": true}',
    
    -- Metadatos
    ip_whitelist JSON DEFAULT NULL COMMENT 'Lista de IPs permitidas (NULL = todas)',
    dominios_permitidos JSON DEFAULT NULL COMMENT 'Dominios permitidos para CORS',
    
    -- Auditoría
    created_by_user INT DEFAULT NULL COMMENT 'Usuario que creó esta API key',
    ultima_modificacion DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices para optimización
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_api_key (api_key),
    INDEX idx_tenant_activa (tenant_id, activa),
    INDEX idx_activa_expiracion (activa, fecha_expiracion),
    
    -- Relaciones
    FOREIGN KEY (tenant_id) REFERENCES Users(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_user) REFERENCES Users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='API Keys públicas para que cada tenant comparta datos de forma segura';

-- Tabla de logs de uso de API Keys
CREATE TABLE IF NOT EXISTS API_Key_Logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    api_key_id INT NOT NULL,
    tenant_id INT NOT NULL,
    
    -- Información de la petición
    endpoint VARCHAR(255) NOT NULL COMMENT 'Endpoint accedido',
    metodo VARCHAR(10) NOT NULL COMMENT 'GET, POST, etc.',
    
    -- Resultado
    status_code INT NOT NULL COMMENT 'Código HTTP de respuesta',
    exitoso BOOLEAN NOT NULL COMMENT 'Si la petición fue exitosa',
    
    -- Detalles de la petición
    ip_origen VARCHAR(45) NOT NULL COMMENT 'IP desde donde se hizo la petición',
    user_agent TEXT DEFAULT NULL COMMENT 'User agent del cliente',
    
    -- Datos de la petición (opcional, para debugging)
    query_params JSON DEFAULT NULL COMMENT 'Parámetros de la petición',
    error_message TEXT DEFAULT NULL COMMENT 'Mensaje de error si falló',
    
    -- Tiempo de respuesta
    response_time_ms INT DEFAULT NULL COMMENT 'Tiempo de respuesta en milisegundos',
    
    -- Timestamp
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices para consultas rápidas
    INDEX idx_api_key_id (api_key_id),
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_exitoso (exitoso),
    INDEX idx_endpoint (endpoint),
    
    -- Relaciones
    FOREIGN KEY (api_key_id) REFERENCES Tenant_API_Keys(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES Users(tenant_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Logs de uso de las API Keys para auditoría y monitoreo';

-- Tabla de rate limiting (control de límites por minuto/hora)
CREATE TABLE IF NOT EXISTS API_Key_Rate_Limits (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    api_key_id INT NOT NULL,
    
    -- Ventana de tiempo
    ventana_inicio DATETIME NOT NULL COMMENT 'Inicio de la ventana de tiempo',
    ventana_tipo ENUM('minute', 'hour', 'day') NOT NULL DEFAULT 'minute',
    
    -- Contador
    request_count INT NOT NULL DEFAULT 1,
    
    -- Índices
    INDEX idx_api_key_ventana (api_key_id, ventana_inicio, ventana_tipo),
    
    -- Relaciones
    FOREIGN KEY (api_key_id) REFERENCES Tenant_API_Keys(id) ON DELETE CASCADE,
    
    -- Clave única para evitar duplicados
    UNIQUE KEY uk_api_key_ventana (api_key_id, ventana_inicio, ventana_tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Control de rate limiting para API Keys';

-- ===============================================================
-- DATOS INICIALES Y CONFIGURACIÓN
-- ===============================================================

-- Insertar permisos por defecto para API Keys (opcional)
-- Esto se puede usar para definir qué endpoints están disponibles
CREATE TABLE IF NOT EXISTS API_Endpoints_Disponibles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    endpoint_key VARCHAR(50) NOT NULL UNIQUE COMMENT 'Identificador del endpoint',
    endpoint_path VARCHAR(255) NOT NULL COMMENT 'Ruta del endpoint',
    descripcion TEXT NOT NULL COMMENT 'Descripción de qué hace este endpoint',
    activo BOOLEAN DEFAULT TRUE,
    
    INDEX idx_endpoint_key (endpoint_key),
    INDEX idx_activo (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Catálogo de endpoints disponibles para las API Keys';

-- Insertar endpoints disponibles
INSERT INTO API_Endpoints_Disponibles (endpoint_key, endpoint_path, descripcion) VALUES
('get_vacancies', '/public-api/v1/vacancies', 'Obtener lista de vacantes activas del tenant'),
('create_candidate', '/public-api/v1/candidates', 'Registrar nuevo candidato con CV en el sistema')
ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion);

-- ===============================================================
-- PROCEDIMIENTOS ALMACENADOS ÚTILES
-- ===============================================================

-- Procedimiento para limpiar logs antiguos (ejecutar periódicamente)
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS cleanup_api_logs(IN dias_antiguedad INT)
BEGIN
    DELETE FROM API_Key_Logs 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL dias_antiguedad DAY);
    
    DELETE FROM API_Key_Rate_Limits 
    WHERE ventana_inicio < DATE_SUB(NOW(), INTERVAL 7 DAY);
END //
DELIMITER ;

-- Procedimiento para obtener estadísticas de una API Key
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS get_api_key_stats(IN p_api_key_id INT)
BEGIN
    SELECT 
        COUNT(*) as total_requests,
        SUM(CASE WHEN exitoso = 1 THEN 1 ELSE 0 END) as requests_exitosos,
        SUM(CASE WHEN exitoso = 0 THEN 1 ELSE 0 END) as requests_fallidos,
        AVG(response_time_ms) as avg_response_time,
        MAX(timestamp) as ultimo_uso
    FROM API_Key_Logs
    WHERE api_key_id = p_api_key_id;
END //
DELIMITER ;

-- ===============================================================
-- ÍNDICES ADICIONALES PARA OPTIMIZACIÓN
-- ===============================================================

-- Índice compuesto para búsquedas frecuentes
CREATE INDEX idx_tenant_activa_expiracion ON Tenant_API_Keys(tenant_id, activa, fecha_expiracion);

-- Índice para logs por fecha
CREATE INDEX idx_logs_fecha_tenant ON API_Key_Logs(tenant_id, timestamp DESC);

-- ===============================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ===============================================================

-- Esta estructura permite:
-- 1. Cada tenant puede tener múltiples API Keys
-- 2. Control granular de permisos por API Key
-- 3. Rate limiting configurable
-- 4. Auditoría completa de uso
-- 5. Expiración automática de keys
-- 6. Whitelist de IPs y dominios
-- 7. Estadísticas de uso en tiempo real

-- ===============================================================
-- FIN DEL SCRIPT
-- ===============================================================
