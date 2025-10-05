-- Tabla para almacenar información de CVs en OCI Object Storage
CREATE TABLE IF NOT EXISTS Candidatos_CVs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    candidate_id INT,
    cv_identifier VARCHAR(255) NOT NULL UNIQUE,
    original_filename VARCHAR(255) NOT NULL,
    object_key VARCHAR(500) NOT NULL,
    file_url TEXT NOT NULL, -- URL de la PAR
    par_id VARCHAR(255),
    mime_type VARCHAR(100),
    file_size BIGINT,
    processing_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    processed_data JSON,
    last_processed TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices para optimización
    INDEX idx_tenant_candidate (tenant_id, candidate_id),
    INDEX idx_cv_identifier (cv_identifier),
    INDEX idx_processing_status (processing_status),
    INDEX idx_created_at (created_at),
    
    -- Claves foráneas (ajustar según tu esquema)
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES Afiliados(id_afiliado) ON DELETE SET NULL
);

-- Tabla para almacenar metadatos de procesamiento de CVs
CREATE TABLE IF NOT EXISTS CV_Processing_Logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    cv_identifier VARCHAR(255) NOT NULL,
    processing_type ENUM('initial_upload', 'reprocess', 'gemini_analysis') NOT NULL,
    status ENUM('started', 'completed', 'failed') NOT NULL,
    error_message TEXT,
    processing_time_ms INT,
    gemini_response JSON,
    extracted_text_length INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_tenant_cv (tenant_id, cv_identifier),
    INDEX idx_status (status),
    INDEX idx_processing_type (processing_type),
    
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (cv_identifier) REFERENCES Candidatos_CVs(cv_identifier) ON DELETE CASCADE
);

-- Tabla para almacenar configuración de OCI por tenant
CREATE TABLE IF NOT EXISTS Tenant_OCI_Config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL UNIQUE,
    oci_namespace VARCHAR(100),
    oci_bucket_name VARCHAR(100) DEFAULT 'crm-cvs',
    oci_region VARCHAR(50) DEFAULT 'us-ashburn-1',
    par_expiration_years INT DEFAULT 10,
    auto_process_cvs BOOLEAN DEFAULT TRUE,
    allowed_file_types JSON DEFAULT '["pdf", "docx", "doc"]',
    max_file_size_mb INT DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
);

-- Insertar configuración por defecto para todos los tenants existentes
INSERT IGNORE INTO Tenant_OCI_Config (tenant_id)
SELECT id FROM Tenants;

-- Vista para obtener información completa de CVs con candidatos
CREATE OR REPLACE VIEW CV_Details_View AS
SELECT 
    ccv.id,
    ccv.tenant_id,
    ccv.candidate_id,
    ccv.cv_identifier,
    ccv.original_filename,
    ccv.object_key,
    ccv.file_url,
    ccv.mime_type,
    ccv.file_size,
    ccv.processing_status,
    ccv.created_at,
    ccv.updated_at,
    a.nombre_completo as candidate_name,
    a.email as candidate_email,
    t.empresa_nombre as tenant_name,
    CASE 
        WHEN ccv.mime_type = 'application/pdf' THEN 'PDF'
        WHEN ccv.mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' THEN 'DOCX'
        WHEN ccv.mime_type = 'application/msword' THEN 'DOC'
        ELSE 'Unknown'
    END as file_type_display,
    ROUND(ccv.file_size / 1024, 2) as file_size_kb
FROM Candidatos_CVs ccv
LEFT JOIN Afiliados a ON ccv.candidate_id = a.id_afiliado AND ccv.tenant_id = a.tenant_id
LEFT JOIN Tenants t ON ccv.tenant_id = t.id;

-- Procedimiento para limpiar CVs antiguos y PARs expiradas
DELIMITER //
CREATE PROCEDURE CleanupExpiredCVs()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE cv_identifier_var VARCHAR(255);
    DECLARE object_key_var VARCHAR(500);
    DECLARE tenant_id_var INT;
    
    -- Cursor para CVs que podrían necesitar limpieza
    DECLARE cv_cursor CURSOR FOR 
        SELECT cv_identifier, object_key, tenant_id 
        FROM Candidatos_CVs 
        WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN cv_cursor;
    
    cleanup_loop: LOOP
        FETCH cv_cursor INTO cv_identifier_var, object_key_var, tenant_id_var;
        IF done THEN
            LEAVE cleanup_loop;
        END IF;
        
        -- Aquí podrías agregar lógica para verificar si la PAR ha expirado
        -- y eliminar el objeto de OCI si es necesario
        
        -- Por ahora, solo registramos en el log
        INSERT INTO CV_Processing_Logs (
            tenant_id, 
            cv_identifier, 
            processing_type, 
            status, 
            error_message
        ) VALUES (
            tenant_id_var,
            cv_identifier_var,
            'reprocess',
            'completed',
            'CV marked for potential cleanup - older than 1 year'
        );
        
    END LOOP;
    
    CLOSE cv_cursor;
END//
DELIMITER ;

-- Evento para ejecutar limpieza automática (opcional)
-- CREATE EVENT IF NOT EXISTS cleanup_cvs_event
-- ON SCHEDULE EVERY 1 MONTH
-- DO CALL CleanupExpiredCVs();

-- Índices adicionales para optimización
CREATE INDEX IF NOT EXISTS idx_cv_processing_logs_tenant_created 
ON CV_Processing_Logs(tenant_id, created_at);

CREATE INDEX IF NOT EXISTS idx_cv_processing_logs_status_created 
ON CV_Processing_Logs(status, created_at);

-- Comentarios para documentación
ALTER TABLE Candidatos_CVs COMMENT = 'Almacena información de CVs subidos a OCI Object Storage';
ALTER TABLE CV_Processing_Logs COMMENT = 'Registra logs de procesamiento de CVs con Gemini AI';
ALTER TABLE Tenant_OCI_Config COMMENT = 'Configuración específica de OCI por tenant';

