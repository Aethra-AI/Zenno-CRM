"""
Crear Tablas para WhatsApp Web.js Multi-Tenant
=============================================
Crea las tablas necesarias para el sistema de WhatsApp Web.js multi-tenant.
"""

import mysql.connector
from mysql.connector import Error

def create_whatsapp_web_tables():
    """Crear tablas para WhatsApp Web.js multi-tenant"""
    
    db_config = {
        'host': 'localhost',
        'database': 'reclutamiento_db',
        'user': 'root',
        'password': 'admin123'
    }
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("🚀 Creando tablas para WhatsApp Web.js multi-tenant...")
        
        # Tabla para sesiones de WhatsApp Web.js
        create_web_sessions_table = """
        CREATE TABLE IF NOT EXISTS WhatsApp_Web_Sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tenant_id INT NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            status ENUM('initializing', 'connecting', 'ready', 'error', 'closed') DEFAULT 'initializing',
            qr_code TEXT NULL,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_tenant_session (tenant_id, session_id),
            INDEX idx_tenant_status (tenant_id, status),
            INDEX idx_last_activity (last_activity),
            UNIQUE KEY unique_tenant_session (tenant_id, session_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # Tabla para logs de actividad de WhatsApp Web.js
        create_web_activity_table = """
        CREATE TABLE IF NOT EXISTS WhatsApp_Web_Activity (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tenant_id INT NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            activity_type ENUM('session_start', 'session_end', 'qr_generated', 'qr_scanned', 
                              'message_sent', 'message_received', 'error', 'connection_lost') NOT NULL,
            activity_data JSON NULL,
            message TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_tenant_session (tenant_id, session_id),
            INDEX idx_activity_type (activity_type),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # Tabla para configuración específica de WhatsApp Web.js por tenant
        create_web_config_table = """
        CREATE TABLE IF NOT EXISTS WhatsApp_Web_Config (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tenant_id INT NOT NULL,
            auto_start BOOLEAN DEFAULT TRUE,
            auto_reconnect BOOLEAN DEFAULT TRUE,
            max_reconnect_attempts INT DEFAULT 5,
            session_timeout_minutes INT DEFAULT 1440, -- 24 horas
            proxy_config JSON NULL,
            puppeteer_options JSON NULL,
            custom_user_agent VARCHAR(500) NULL,
            headless_mode BOOLEAN DEFAULT TRUE,
            webhook_url VARCHAR(500) NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_tenant_web_config (tenant_id),
            INDEX idx_tenant_active (tenant_id, is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # Tabla para estadísticas de WhatsApp Web.js por tenant
        create_web_stats_table = """
        CREATE TABLE IF NOT EXISTS WhatsApp_Web_Stats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tenant_id INT NOT NULL,
            session_id VARCHAR(255) NULL,
            date DATE NOT NULL,
            messages_sent INT DEFAULT 0,
            messages_received INT DEFAULT 0,
            sessions_started INT DEFAULT 0,
            sessions_ended INT DEFAULT 0,
            connection_errors INT DEFAULT 0,
            total_uptime_minutes INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_tenant_date_session (tenant_id, date, session_id),
            INDEX idx_tenant_date (tenant_id, date),
            INDEX idx_date (date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # Ejecutar creación de tablas
        tables = [
            ("WhatsApp_Web_Sessions", create_web_sessions_table),
            ("WhatsApp_Web_Activity", create_web_activity_table),
            ("WhatsApp_Web_Config", create_web_config_table),
            ("WhatsApp_Web_Stats", create_web_stats_table)
        ]
        
        for table_name, create_sql in tables:
            try:
                cursor.execute(create_sql)
                print(f"✅ Tabla {table_name} creada exitosamente")
            except Error as e:
                if e.errno == 1050:  # Table already exists
                    print(f"⚠️ Tabla {table_name} ya existe")
                else:
                    print(f"❌ Error creando tabla {table_name}: {e}")
        
        # Insertar configuración por defecto para tenant 1
        try:
            insert_default_config = """
            INSERT IGNORE INTO WhatsApp_Web_Config 
            (tenant_id, auto_start, auto_reconnect, max_reconnect_attempts, session_timeout_minutes, is_active)
            VALUES (1, TRUE, TRUE, 5, 1440, TRUE)
            """
            cursor.execute(insert_default_config)
            print("✅ Configuración por defecto insertada para tenant 1")
        except Error as e:
            print(f"⚠️ Configuración por defecto ya existe: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n🎉 ¡Tablas de WhatsApp Web.js creadas exitosamente!")
        print("\n📋 Tablas creadas:")
        print("   • WhatsApp_Web_Sessions - Sesiones activas por tenant")
        print("   • WhatsApp_Web_Activity - Logs de actividad")
        print("   • WhatsApp_Web_Config - Configuración por tenant")
        print("   • WhatsApp_Web_Stats - Estadísticas de uso")
        
        return True
        
    except Error as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False

if __name__ == "__main__":
    create_whatsapp_web_tables()

