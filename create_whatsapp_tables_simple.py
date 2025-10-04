#!/usr/bin/env python3
"""
📱 CREAR TABLAS WHATSAPP MULTI-TENANT - VERSIÓN SIMPLE
======================================================

Script simplificado para crear las tablas principales
necesarias para el sistema WhatsApp multi-tenant.
"""

import mysql.connector
import os
from dotenv import load_dotenv
import logging

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'crm_db'),
            charset='utf8mb4'
        )
    except Exception as e:
        logger.error(f"❌ Error conectando a BD: {str(e)}")
        raise

def create_whatsapp_config_table():
    """Crear tabla de configuración WhatsApp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Eliminar tabla si existe
        cursor.execute("DROP TABLE IF EXISTS WhatsApp_Config")
        
        # Crear tabla
        cursor.execute("""
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
            )
        """)
        
        conn.commit()
        logger.info("✅ Tabla WhatsApp_Config creada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error creando WhatsApp_Config: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

def create_whatsapp_conversations_table():
    """Crear tabla de conversaciones WhatsApp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Eliminar tabla si existe
        cursor.execute("DROP TABLE IF EXISTS WhatsApp_Conversations")
        
        # Crear tabla
        cursor.execute("""
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
            )
        """)
        
        conn.commit()
        logger.info("✅ Tabla WhatsApp_Conversations creada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error creando WhatsApp_Conversations: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

def create_whatsapp_messages_table():
    """Crear tabla de mensajes WhatsApp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Eliminar tabla si existe
        cursor.execute("DROP TABLE IF EXISTS WhatsApp_Messages")
        
        # Crear tabla
        cursor.execute("""
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
                wa_timestamp TIMESTAMP NULL,
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
            )
        """)
        
        conn.commit()
        logger.info("✅ Tabla WhatsApp_Messages creada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error creando WhatsApp_Messages: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

def create_whatsapp_templates_table():
    """Crear tabla de plantillas WhatsApp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Eliminar tabla si existe
        cursor.execute("DROP TABLE IF EXISTS WhatsApp_Templates")
        
        # Crear tabla
        cursor.execute("""
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
            )
        """)
        
        conn.commit()
        logger.info("✅ Tabla WhatsApp_Templates creada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error creando WhatsApp_Templates: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

def insert_initial_data():
    """Insertar datos iniciales"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insertar plantillas por defecto
        cursor.execute("""
            INSERT INTO WhatsApp_Templates (tenant_id, name, category, subject, content, is_default, is_active) VALUES
            (1, 'Postulación Recibida', 'postulation', 'Postulación Recibida', 'Hola {{nombre}}, hemos recibido tu postulación para la vacante de {{cargo}}. Te contactaremos pronto con más información. ¡Gracias por tu interés!', TRUE, TRUE),
            (1, 'Entrevista Programada', 'interview', 'Entrevista Programada', 'Hola {{nombre}}, tu entrevista para {{cargo}} está programada para el {{fecha}} a las {{hora}}. Por favor confirma tu asistencia.', TRUE, TRUE),
            (1, 'Candidato Contratado', 'hiring', '¡Felicitaciones!', 'Hola {{nombre}}, ¡felicitaciones! Has sido seleccionado para el puesto de {{cargo}}. Te contactaremos pronto con los detalles de tu incorporación.', TRUE, TRUE),
            (1, 'Recordatorio de Entrevista', 'reminder', 'Recordatorio de Entrevista', 'Hola {{nombre}}, te recordamos que tienes una entrevista mañana a las {{hora}} para {{cargo}}. ¡Te esperamos!', TRUE, TRUE)
        """)
        
        conn.commit()
        logger.info("✅ Datos iniciales insertados exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error insertando datos iniciales: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

def verify_tables():
    """Verificar que las tablas se crearon correctamente"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        logger.info("🔍 Verificando estructura de tablas...")
        
        # Verificar tabla principal
        cursor.execute("DESCRIBE WhatsApp_Config")
        config_columns = cursor.fetchall()
        logger.info(f"📋 WhatsApp_Config: {len(config_columns)} columnas")
        
        cursor.execute("DESCRIBE WhatsApp_Conversations")
        conv_columns = cursor.fetchall()
        logger.info(f"💬 WhatsApp_Conversations: {len(conv_columns)} columnas")
        
        cursor.execute("DESCRIBE WhatsApp_Messages")
        msg_columns = cursor.fetchall()
        logger.info(f"📨 WhatsApp_Messages: {len(msg_columns)} columnas")
        
        cursor.execute("DESCRIBE WhatsApp_Templates")
        template_columns = cursor.fetchall()
        logger.info(f"📝 WhatsApp_Templates: {len(template_columns)} columnas")
        
        # Verificar datos iniciales
        cursor.execute("SELECT COUNT(*) as count FROM WhatsApp_Templates")
        template_count = cursor.fetchone()
        logger.info(f"📝 Plantillas iniciales: {template_count['count']}")
        
        logger.info("✅ Verificación completada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error verificando tablas: {str(e)}")
        
    finally:
        cursor.close()
        conn.close()

def main():
    """Función principal"""
    logger.info("🚀 INICIANDO CREACIÓN SIMPLE DE TABLAS WHATSAPP")
    logger.info("=" * 60)
    
    try:
        # Crear tablas principales
        create_whatsapp_config_table()
        create_whatsapp_conversations_table()
        create_whatsapp_messages_table()
        create_whatsapp_templates_table()
        
        # Insertar datos iniciales
        insert_initial_data()
        
        logger.info("=" * 60)
        logger.info("🎉 CREACIÓN DE TABLAS COMPLETADA EXITOSAMENTE")
        
        # Verificar tablas
        verify_tables()
        
        logger.info("=" * 60)
        logger.info("✅ SISTEMA WHATSAPP MULTI-TENANT LISTO PARA IMPLEMENTACIÓN")
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ ERROR EN LA CREACIÓN DE TABLAS: {str(e)}")
        logger.error("Revisar logs para más detalles")

if __name__ == "__main__":
    main()
