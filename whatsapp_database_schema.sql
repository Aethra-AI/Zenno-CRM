-- =====================================================
-- 📱 ESQUEMA DE BASE DE DATOS: WHATSAPP MULTI-TENANT
-- =====================================================

-- Tabla principal de configuración WhatsApp por tenant
CREATE TABLE WhatsApp_Config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    api_type ENUM('business_api', 'whatsapp_web') NOT NULL,
    
    -- Configuración Business API
    business_api_token VARCHAR(500),
    phone_number_id VARCHAR(50),
    webhook_verify_token VARCHAR(100),
    business_account_id VARCHAR(50),
    
    -- Configuración WhatsApp Web
    web_session_id VARCHAR(100),
    web_qr_code TEXT,
    web_status ENUM('disconnected', 'qr_ready', 'connected', 'authenticated', 'ready') DEFAULT 'disconnected',
    web_last_seen TIMESTAMP NULL,
    
    -- Configuración común
    webhook_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    auto_reconnect BOOLEAN DEFAULT TRUE,
    max_retries INT DEFAULT 3,
    
    -- Metadatos
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices y restricciones
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    UNIQUE KEY unique_tenant_api (tenant_id, api_type),
    INDEX idx_tenant_active (tenant_id, is_active),
    INDEX idx_phone_number (phone_number_id),
    INDEX idx_web_session (web_session_id)
);

-- Tabla de conversaciones WhatsApp
CREATE TABLE WhatsApp_Conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    conversation_id VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    contact_name VARCHAR(100),
    contact_wa_id VARCHAR(50),
    
    -- Información de la conversación
    last_message_at TIMESTAMP NULL,
    last_message_preview TEXT,
    unread_count INT DEFAULT 0,
    message_count INT DEFAULT 0,
    
    -- Estado de la conversación
    status ENUM('active', 'archived', 'blocked', 'muted') DEFAULT 'active',
    is_pinned BOOLEAN DEFAULT FALSE,
    priority ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal',
    
    -- Metadatos
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices y restricciones
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    UNIQUE KEY unique_conversation (tenant_id, conversation_id),
    INDEX idx_tenant_phone (tenant_id, contact_phone),
    INDEX idx_tenant_status (tenant_id, status),
    INDEX idx_last_message (last_message_at),
    INDEX idx_unread (tenant_id, unread_count)
);

-- Tabla de mensajes WhatsApp
CREATE TABLE WhatsApp_Messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    conversation_id INT NOT NULL,
    
    -- IDs de WhatsApp
    message_id VARCHAR(100) NOT NULL,
    wa_message_id VARCHAR(100),
    
    -- Información del mensaje
    direction ENUM('inbound', 'outbound') NOT NULL,
    message_type ENUM('text', 'image', 'document', 'audio', 'video', 'location', 'contact', 'sticker', 'template') NOT NULL,
    content TEXT,
    media_url VARCHAR(500),
    media_mime_type VARCHAR(100),
    media_size INT,
    media_filename VARCHAR(255),
    
    -- Estado del mensaje
    status ENUM('sent', 'delivered', 'read', 'failed', 'pending') DEFAULT 'pending',
    error_code VARCHAR(50),
    error_message TEXT,
    
    -- Metadatos de WhatsApp
    timestamp TIMESTAMP NOT NULL,
    wa_timestamp TIMESTAMP,
    context_message_id VARCHAR(100),
    
    -- Metadatos del sistema
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices y restricciones
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES WhatsApp_Conversations(id) ON DELETE CASCADE,
    UNIQUE KEY unique_message (tenant_id, message_id),
    INDEX idx_conversation_timestamp (conversation_id, timestamp),
    INDEX idx_tenant_timestamp (tenant_id, timestamp),
    INDEX idx_status (status),
    INDEX idx_message_type (message_type),
    INDEX idx_direction (direction)
);

-- Tabla de plantillas de mensajes
CREATE TABLE WhatsApp_Templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    
    -- Información de la plantilla
    name VARCHAR(100) NOT NULL,
    category ENUM('postulation', 'interview', 'hiring', 'general', 'marketing', 'reminder') NOT NULL,
    subject VARCHAR(200),
    content TEXT NOT NULL,
    
    -- Variables dinámicas
    variables JSON,
    
    -- Configuración
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    usage_count INT DEFAULT 0,
    last_used_at TIMESTAMP NULL,
    
    -- Metadatos
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices y restricciones
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES Users(id) ON DELETE SET NULL,
    INDEX idx_tenant_category (tenant_id, category),
    INDEX idx_tenant_active (tenant_id, is_active),
    INDEX idx_usage_count (usage_count)
);

-- Tabla de campañas de WhatsApp
CREATE TABLE WhatsApp_Campaigns (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    
    -- Información de la campaña
    name VARCHAR(200) NOT NULL,
    description TEXT,
    template_id INT,
    custom_message TEXT,
    
    -- Configuración de envío
    target_type ENUM('candidates', 'contacts', 'list') NOT NULL,
    target_criteria JSON,
    target_list JSON,
    
    -- Estado de la campaña
    status ENUM('draft', 'scheduled', 'sending', 'sent', 'failed', 'cancelled') DEFAULT 'draft',
    scheduled_at TIMESTAMP NULL,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    
    -- Estadísticas
    total_recipients INT DEFAULT 0,
    messages_sent INT DEFAULT 0,
    messages_delivered INT DEFAULT 0,
    messages_read INT DEFAULT 0,
    messages_failed INT DEFAULT 0,
    
    -- Metadatos
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices y restricciones
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES WhatsApp_Templates(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES Users(id) ON DELETE SET NULL,
    INDEX idx_tenant_status (tenant_id, status),
    INDEX idx_scheduled (scheduled_at),
    INDEX idx_created_by (created_by)
);

-- Tabla de destinatarios de campañas
CREATE TABLE WhatsApp_Campaign_Recipients (
    id INT PRIMARY KEY AUTO_INCREMENT,
    campaign_id INT NOT NULL,
    tenant_id INT NOT NULL,
    
    -- Información del destinatario
    recipient_type ENUM('candidate', 'contact', 'custom') NOT NULL,
    recipient_id INT,
    phone_number VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    
    -- Estado del envío
    status ENUM('pending', 'sent', 'delivered', 'read', 'failed') DEFAULT 'pending',
    message_id VARCHAR(100),
    error_code VARCHAR(50),
    error_message TEXT,
    
    -- Timestamps
    sent_at TIMESTAMP NULL,
    delivered_at TIMESTAMP NULL,
    read_at TIMESTAMP NULL,
    
    -- Metadatos
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices y restricciones
    FOREIGN KEY (campaign_id) REFERENCES WhatsApp_Campaigns(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    INDEX idx_campaign_status (campaign_id, status),
    INDEX idx_tenant_phone (tenant_id, phone_number),
    INDEX idx_sent_at (sent_at)
);

-- Tabla de webhooks recibidos
CREATE TABLE WhatsApp_Webhooks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    
    -- Información del webhook
    webhook_type ENUM('message', 'status', 'template', 'account_update') NOT NULL,
    phone_number_id VARCHAR(50),
    raw_data JSON NOT NULL,
    
    -- Procesamiento
    processed BOOLEAN DEFAULT FALSE,
    processing_error TEXT,
    
    -- Metadatos
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    
    -- Índices y restricciones
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    INDEX idx_tenant_type (tenant_id, webhook_type),
    INDEX idx_processed (processed),
    INDEX idx_received_at (received_at)
);

-- Tabla de logs de actividad
CREATE TABLE WhatsApp_Activity_Logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    
    -- Información de la actividad
    activity_type ENUM('message_sent', 'message_received', 'conversation_started', 'conversation_ended', 'campaign_started', 'campaign_completed', 'connection_status', 'error') NOT NULL,
    description TEXT,
    
    -- Datos relacionados
    related_id INT,
    related_type ENUM('message', 'conversation', 'campaign', 'template') NULL,
    
    -- Metadatos adicionales
    metadata JSON,
    
    -- Metadatos
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices y restricciones
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE SET NULL,
    INDEX idx_tenant_activity (tenant_id, activity_type),
    INDEX idx_created_at (created_at),
    INDEX idx_related (related_type, related_id)
);

-- Tabla de configuración de notificaciones automáticas
CREATE TABLE WhatsApp_Notification_Rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    
    -- Información de la regla
    name VARCHAR(200) NOT NULL,
    description TEXT,
    trigger_event ENUM('candidate_postulated', 'interview_scheduled', 'candidate_hired', 'status_changed', 'custom') NOT NULL,
    
    -- Condiciones
    conditions JSON,
    
    -- Configuración de envío
    template_id INT,
    custom_message TEXT,
    delay_minutes INT DEFAULT 0,
    
    -- Estado
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMP NULL,
    trigger_count INT DEFAULT 0,
    
    -- Metadatos
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices y restricciones
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES WhatsApp_Templates(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES Users(id) ON DELETE SET NULL,
    INDEX idx_tenant_trigger (tenant_id, trigger_event),
    INDEX idx_tenant_active (tenant_id, is_active)
);

-- =====================================================
-- 📊 VISTAS ÚTILES
-- =====================================================

-- Vista de conversaciones activas con información resumida
CREATE VIEW v_whatsapp_active_conversations AS
SELECT 
    wc.id,
    wc.tenant_id,
    wc.conversation_id,
    wc.contact_phone,
    wc.contact_name,
    wc.last_message_at,
    wc.last_message_preview,
    wc.unread_count,
    wc.status,
    wc.is_pinned,
    wc.priority,
    t.nombre_empresa as tenant_name
FROM WhatsApp_Conversations wc
JOIN Tenants t ON wc.tenant_id = t.id
WHERE wc.status = 'active'
ORDER BY wc.last_message_at DESC;

-- Vista de estadísticas por tenant
CREATE VIEW v_whatsapp_tenant_stats AS
SELECT 
    t.id as tenant_id,
    t.nombre_empresa,
    COUNT(DISTINCT wc.id) as total_conversations,
    COUNT(DISTINCT CASE WHEN wc.status = 'active' THEN wc.id END) as active_conversations,
    COUNT(DISTINCT wm.id) as total_messages,
    COUNT(DISTINCT CASE WHEN wm.direction = 'inbound' THEN wm.id END) as messages_received,
    COUNT(DISTINCT CASE WHEN wm.direction = 'outbound' THEN wm.id END) as messages_sent,
    COUNT(DISTINCT CASE WHEN DATE(wm.created_at) = CURDATE() THEN wm.id END) as messages_today,
    MAX(wm.created_at) as last_activity
FROM Tenants t
LEFT JOIN WhatsApp_Conversations wc ON t.id = wc.tenant_id
LEFT JOIN WhatsApp_Messages wm ON wc.id = wm.conversation_id
GROUP BY t.id, t.nombre_empresa;

-- Vista de mensajes recientes por conversación
CREATE VIEW v_whatsapp_recent_messages AS
SELECT 
    wm.id,
    wm.tenant_id,
    wm.conversation_id,
    wc.contact_phone,
    wc.contact_name,
    wm.direction,
    wm.message_type,
    wm.content,
    wm.status,
    wm.timestamp,
    wm.created_at
FROM WhatsApp_Messages wm
JOIN WhatsApp_Conversations wc ON wm.conversation_id = wc.id
WHERE wm.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY wm.created_at DESC;

-- =====================================================
-- 🔧 PROCEDIMIENTOS ALMACENADOS
-- =====================================================

-- Procedimiento para limpiar mensajes antiguos
DELIMITER //
CREATE PROCEDURE CleanupOldWhatsAppMessages(IN days_to_keep INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Eliminar mensajes antiguos
    DELETE FROM WhatsApp_Messages 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY)
    AND status IN ('delivered', 'read', 'failed');
    
    -- Eliminar conversaciones sin mensajes
    DELETE FROM WhatsApp_Conversations 
    WHERE id NOT IN (SELECT DISTINCT conversation_id FROM WhatsApp_Messages)
    AND last_message_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    -- Eliminar webhooks procesados antiguos
    DELETE FROM WhatsApp_Webhooks 
    WHERE processed = TRUE 
    AND received_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    COMMIT;
END //
DELIMITER ;

-- Procedimiento para actualizar estadísticas de conversación
DELIMITER //
CREATE PROCEDURE UpdateConversationStats(IN conv_id INT)
BEGIN
    DECLARE msg_count INT;
    DECLARE unread_count INT;
    DECLARE last_msg_at TIMESTAMP;
    DECLARE last_msg_preview TEXT;
    
    -- Contar mensajes totales
    SELECT COUNT(*) INTO msg_count
    FROM WhatsApp_Messages 
    WHERE conversation_id = conv_id;
    
    -- Contar mensajes no leídos (inbound y no leídos)
    SELECT COUNT(*) INTO unread_count
    FROM WhatsApp_Messages 
    WHERE conversation_id = conv_id 
    AND direction = 'inbound' 
    AND status NOT IN ('read');
    
    -- Obtener último mensaje
    SELECT timestamp, content INTO last_msg_at, last_msg_preview
    FROM WhatsApp_Messages 
    WHERE conversation_id = conv_id 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    -- Actualizar conversación
    UPDATE WhatsApp_Conversations 
    SET 
        message_count = msg_count,
        unread_count = unread_count,
        last_message_at = last_msg_at,
        last_message_preview = LEFT(last_msg_preview, 100),
        updated_at = NOW()
    WHERE id = conv_id;
END //
DELIMITER ;

-- =====================================================
-- 🔄 TRIGGERS
-- =====================================================

-- Trigger para actualizar estadísticas cuando se inserta un mensaje
DELIMITER //
CREATE TRIGGER tr_whatsapp_message_insert
AFTER INSERT ON WhatsApp_Messages
FOR EACH ROW
BEGIN
    CALL UpdateConversationStats(NEW.conversation_id);
END //
DELIMITER ;

-- Trigger para actualizar estadísticas cuando se actualiza un mensaje
DELIMITER //
CREATE TRIGGER tr_whatsapp_message_update
AFTER UPDATE ON WhatsApp_Messages
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        CALL UpdateConversationStats(NEW.conversation_id);
    END IF;
END //
DELIMITER ;

-- =====================================================
-- 📝 DATOS INICIALES
-- =====================================================

-- Insertar plantillas por defecto
INSERT INTO WhatsApp_Templates (tenant_id, name, category, subject, content, is_default, is_active) VALUES
(1, 'Postulación Recibida', 'postulation', 'Postulación Recibida', 'Hola {{nombre}}, hemos recibido tu postulación para la vacante de {{cargo}}. Te contactaremos pronto con más información. ¡Gracias por tu interés!', TRUE, TRUE),
(1, 'Entrevista Programada', 'interview', 'Entrevista Programada', 'Hola {{nombre}}, tu entrevista para {{cargo}} está programada para el {{fecha}} a las {{hora}}. Por favor confirma tu asistencia.', TRUE, TRUE),
(1, 'Candidato Contratado', 'hiring', '¡Felicitaciones!', 'Hola {{nombre}}, ¡felicitaciones! Has sido seleccionado para el puesto de {{cargo}}. Te contactaremos pronto con los detalles de tu incorporación.', TRUE, TRUE),
(1, 'Recordatorio de Entrevista', 'reminder', 'Recordatorio de Entrevista', 'Hola {{nombre}}, te recordamos que tienes una entrevista mañana a las {{hora}} para {{cargo}}. ¡Te esperamos!', TRUE, TRUE);

-- Insertar reglas de notificación por defecto
INSERT INTO WhatsApp_Notification_Rules (tenant_id, name, description, trigger_event, template_id, is_active) VALUES
(1, 'Notificación de Postulación', 'Notifica automáticamente cuando un candidato se postula', 'candidate_postulated', 1, TRUE),
(1, 'Notificación de Entrevista', 'Notifica cuando se programa una entrevista', 'interview_scheduled', 2, TRUE),
(1, 'Notificación de Contratación', 'Notifica cuando se contrata un candidato', 'candidate_hired', 3, TRUE),
(1, 'Recordatorio de Entrevista', 'Envía recordatorio 24h antes de la entrevista', 'interview_scheduled', 4, TRUE);

-- =====================================================
-- 📊 ÍNDICES ADICIONALES PARA RENDIMIENTO
-- =====================================================

-- Índices compuestos para consultas frecuentes
CREATE INDEX idx_messages_tenant_time ON WhatsApp_Messages(tenant_id, created_at DESC);
CREATE INDEX idx_conversations_tenant_phone ON WhatsApp_Conversations(tenant_id, contact_phone);
CREATE INDEX idx_campaigns_tenant_status ON WhatsApp_Campaigns(tenant_id, status);
CREATE INDEX idx_templates_tenant_category ON WhatsApp_Templates(tenant_id, category, is_active);

-- =====================================================
-- 🔐 COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

/*
ESQUEMA DE BASE DE DATOS WHATSAPP MULTI-TENANT

Este esquema proporciona:
- Aislamiento completo por tenant
- Soporte para WhatsApp Business API y WhatsApp Web
- Gestión de conversaciones y mensajes
- Sistema de plantillas y campañas
- Notificaciones automáticas
- Logs y auditoría
- Vistas optimizadas para consultas frecuentes
- Procedimientos para mantenimiento

CARACTERÍSTICAS PRINCIPALES:
✅ Multi-tenancy completo
✅ Soporte dual (API + Web)
✅ Escalabilidad empresarial
✅ Auditoría y logs
✅ Optimización de rendimiento
✅ Integridad referencial
✅ Limpieza automática de datos

MANTENIMIENTO:
- Ejecutar CleanupOldWhatsAppMessages(90) mensualmente
- Monitorear índices y estadísticas
- Revisar logs de actividad regularmente
*/
