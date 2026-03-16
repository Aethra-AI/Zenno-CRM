"""
Sistema de Migraciones Automáticas para el CRM
Ejecuta migraciones pendientes al iniciar el servidor
"""

import mysql.connector
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseMigrations:
    def __init__(self, db_config):
        """
        Inicializar el sistema de migraciones
        
        Args:
            db_config: Diccionario con configuración de la base de datos
                      {'host', 'user', 'password', 'database'}
        """
        self.db_config = db_config
        self.migrations = []
        self._register_migrations()
    
    def _register_migrations(self):
        """Registrar todas las migraciones disponibles"""
        
        # Migración 1: Sistema de API Keys Públicas
        self.migrations.append({
            'id': 1,
            'name': 'create_public_api_keys_system',
            'description': 'Crear sistema de API Keys públicas para multi-tenant',
            'execute': self._migration_001_api_keys
        })
        
        # Migración 2: Aumentar tamaño de columna api_key
        self.migrations.append({
            'id': 3,
            'name': 'fix_tenant_api_key_column_size',
            'description': 'Aumentar tamaño de columna api_key en Tenant_API_Keys de VARCHAR(64) a VARCHAR(255)',
            'execute': self._migration_002_fix_api_key_size
        })
    
        # Migración 4: Seed de permisos por pestañas para roles base
        self.migrations.append({
            'id': 4,
            'name': 'seed_role_permissions_tabs_v1',
            'description': 'Poblar Roles.permisos con esquema por pestañas para Admin/Supervisor/Reclutador',
            'execute': self._migration_004_seed_role_permissions
        })

        # Migración 5: Crear tabla WhatsApp_Web_Sessions
        self.migrations.append({
            'id': 5,
            'name': 'create_whatsapp_web_sessions_table',
            'description': 'Crear tabla para sesiones de WhatsApp Web',
            'execute': self._migration_005_create_whatsapp_web_sessions
        })

        # Migración 6: Sistema de Persistencia de Chat para Agentes (IDE UX)
        self.migrations.append({
            'id': 6,
            'name': 'create_agent_chat_persistence_tables',
            'description': 'Crear tablas AgentSessions y AgentMessages para historial centralizado tipo IDE',
            'execute': self._migration_006_agent_sessions
        })
    
    def _create_migrations_table(self, conn):
        """Crear tabla para trackear migraciones ejecutadas"""
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Database_Migrations (
                id INT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                execution_time_ms INT,
                status ENUM('success', 'failed') DEFAULT 'success',
                error_message TEXT,
                
                INDEX idx_name (name),
                INDEX idx_executed_at (executed_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='Control de migraciones ejecutadas en la base de datos'
        """)
        
        conn.commit()
        cursor.close()
        logger.info("✅ Tabla Database_Migrations creada/verificada")
    
    def _is_migration_executed(self, conn, migration_id):
        """Verificar si una migración ya fue ejecutada"""
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, status FROM Database_Migrations 
            WHERE id = %s
        """, (migration_id,))
        
        result = cursor.fetchone()
        cursor.close()
        
        return result is not None and result['status'] == 'success'
    
    def _mark_migration_executed(self, conn, migration_id, name, description, 
                                 execution_time_ms, status='success', error_message=None):
        """Marcar una migración como ejecutada"""
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Database_Migrations 
            (id, name, description, execution_time_ms, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                executed_at = CURRENT_TIMESTAMP,
                execution_time_ms = VALUES(execution_time_ms),
                status = VALUES(status),
                error_message = VALUES(error_message)
        """, (migration_id, name, description, execution_time_ms, status, error_message))
        
        conn.commit()
        cursor.close()
    
    def run_pending_migrations(self):
        """Ejecutar todas las migraciones pendientes"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            
            # Crear tabla de control de migraciones
            self._create_migrations_table(conn)
            
            # Ejecutar migraciones pendientes
            for migration in self.migrations:
                migration_id = migration['id']
                migration_name = migration['name']
                migration_desc = migration['description']
                
                if self._is_migration_executed(conn, migration_id):
                    logger.info(f"⏭️  Migración {migration_id} ({migration_name}) ya ejecutada, omitiendo...")
                    continue
                
                logger.info(f"🚀 Ejecutando migración {migration_id}: {migration_name}")
                logger.info(f"   📝 {migration_desc}")
                
                start_time = datetime.now()
                
                try:
                    # Ejecutar la migración
                    migration['execute'](conn)
                    
                    # Calcular tiempo de ejecución
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Marcar como ejecutada
                    self._mark_migration_executed(
                        conn, migration_id, migration_name, migration_desc,
                        int(execution_time), 'success'
                    )
                    
                    logger.info(f"✅ Migración {migration_id} completada en {execution_time:.0f}ms")
                    
                except Exception as e:
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    error_msg = str(e)
                    
                    logger.error(f"❌ Error en migración {migration_id}: {error_msg}")
                    
                    # Marcar como fallida
                    self._mark_migration_executed(
                        conn, migration_id, migration_name, migration_desc,
                        int(execution_time), 'failed', error_msg
                    )
                    
                    # Hacer rollback de esta migración
                    conn.rollback()
                    
                    # No continuar con las siguientes migraciones
                    raise
            
            conn.close()
            logger.info("✅ Todas las migraciones completadas exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando migraciones: {str(e)}")
            return False
    
    # =========================================================================
    # MIGRACIONES INDIVIDUALES
    # =========================================================================
    
    def _migration_001_api_keys(self, conn):
        """
        Migración 001: Sistema de API Keys Públicas
        Crea las tablas necesarias para el sistema de API Keys
        """
        cursor = conn.cursor()
        
        # 0. Crear índice en Users.tenant_id si no existe (necesario para foreign key)
        logger.info("   🔍 Verificando índice en Users.tenant_id...")
        try:
            cursor.execute("""
                CREATE INDEX idx_users_tenant_id ON Users(tenant_id)
            """)
            logger.info("   ✅ Índice en Users.tenant_id creado")
        except mysql.connector.Error as e:
            if e.errno == 1061:  # Error 1061 = índice duplicado
                logger.info("   ⏭️  Índice en Users.tenant_id ya existe")
            else:
                raise
        
        # 1. Tabla principal de API Keys
        logger.info("   📦 Creando tabla Tenant_API_Keys...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Tenant_API_Keys (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tenant_id INT NOT NULL,
                
                api_key VARCHAR(64) NOT NULL UNIQUE COMMENT 'Clave pública (ej: hnm_live_abc123...)',
                api_secret_hash VARCHAR(255) NOT NULL COMMENT 'Hash del secreto (bcrypt)',
                
                nombre_descriptivo VARCHAR(255) DEFAULT NULL COMMENT 'Nombre para identificar el uso de esta key',
                descripcion TEXT DEFAULT NULL COMMENT 'Descripción del propósito de esta API key',
                
                activa BOOLEAN DEFAULT TRUE COMMENT 'Si la key está activa o desactivada',
                
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_expiracion DATETIME DEFAULT NULL COMMENT 'Fecha de expiración (NULL = sin expiración)',
                ultimo_uso DATETIME DEFAULT NULL COMMENT 'Última vez que se usó esta key',
                
                total_requests INT DEFAULT 0 COMMENT 'Total de peticiones realizadas con esta key',
                requests_exitosos INT DEFAULT 0 COMMENT 'Peticiones exitosas',
                requests_fallidos INT DEFAULT 0 COMMENT 'Peticiones fallidas',
                
                rate_limit_per_minute INT DEFAULT 100 COMMENT 'Máximo de requests por minuto',
                rate_limit_per_day INT DEFAULT 10000 COMMENT 'Máximo de requests por día',
                
                permisos JSON DEFAULT NULL COMMENT 'Permisos específicos: {"vacancies": true, "candidates": true}',
                
                ip_whitelist JSON DEFAULT NULL COMMENT 'Lista de IPs permitidas (NULL = todas)',
                dominios_permitidos JSON DEFAULT NULL COMMENT 'Dominios permitidos para CORS',
                
                created_by_user INT DEFAULT NULL COMMENT 'Usuario que creó esta API key',
                ultima_modificacion DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_tenant_id (tenant_id),
                INDEX idx_api_key (api_key),
                INDEX idx_tenant_activa (tenant_id, activa),
                INDEX idx_activa_expiracion (activa, fecha_expiracion),
                
                FOREIGN KEY (tenant_id) REFERENCES Users(tenant_id) ON DELETE CASCADE,
                FOREIGN KEY (created_by_user) REFERENCES Users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='API Keys públicas para que cada tenant comparta datos de forma segura'
        """)
        
        # 2. Tabla de logs
        logger.info("   📦 Creando tabla API_Key_Logs...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS API_Key_Logs (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                api_key_id INT NOT NULL,
                tenant_id INT NOT NULL,
                
                endpoint VARCHAR(255) NOT NULL COMMENT 'Endpoint accedido',
                metodo VARCHAR(10) NOT NULL COMMENT 'GET, POST, etc.',
                
                status_code INT NOT NULL COMMENT 'Código HTTP de respuesta',
                exitoso BOOLEAN NOT NULL COMMENT 'Si la petición fue exitosa',
                
                ip_origen VARCHAR(45) NOT NULL COMMENT 'IP desde donde se hizo la petición',
                user_agent TEXT DEFAULT NULL COMMENT 'User agent del cliente',
                
                query_params JSON DEFAULT NULL COMMENT 'Parámetros de la petición',
                error_message TEXT DEFAULT NULL COMMENT 'Mensaje de error si falló',
                
                response_time_ms INT DEFAULT NULL COMMENT 'Tiempo de respuesta en milisegundos',
                
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_api_key_id (api_key_id),
                INDEX idx_tenant_id (tenant_id),
                INDEX idx_timestamp (timestamp),
                INDEX idx_exitoso (exitoso),
                INDEX idx_endpoint (endpoint),
                
                FOREIGN KEY (api_key_id) REFERENCES Tenant_API_Keys(id) ON DELETE CASCADE,
                FOREIGN KEY (tenant_id) REFERENCES Users(tenant_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='Logs de uso de las API Keys para auditoría y monitoreo'
        """)
        
        # 3. Tabla de rate limiting
        logger.info("   📦 Creando tabla API_Key_Rate_Limits...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS API_Key_Rate_Limits (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                api_key_id INT NOT NULL,
                
                ventana_inicio DATETIME NOT NULL COMMENT 'Inicio de la ventana de tiempo',
                ventana_tipo ENUM('minute', 'hour', 'day') NOT NULL DEFAULT 'minute',
                
                request_count INT NOT NULL DEFAULT 1,
                
                INDEX idx_api_key_ventana (api_key_id, ventana_inicio, ventana_tipo),
                
                FOREIGN KEY (api_key_id) REFERENCES Tenant_API_Keys(id) ON DELETE CASCADE,
                
                UNIQUE KEY uk_api_key_ventana (api_key_id, ventana_inicio, ventana_tipo)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='Control de rate limiting para API Keys'
        """)
        
        # 4. Tabla de endpoints disponibles
        logger.info("   📦 Creando tabla API_Endpoints_Disponibles...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS API_Endpoints_Disponibles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                endpoint_key VARCHAR(50) NOT NULL UNIQUE COMMENT 'Identificador del endpoint',
                endpoint_path VARCHAR(255) NOT NULL COMMENT 'Ruta del endpoint',
                descripcion TEXT NOT NULL COMMENT 'Descripción de qué hace este endpoint',
                activo BOOLEAN DEFAULT TRUE,
                
                INDEX idx_endpoint_key (endpoint_key),
                INDEX idx_activo (activo)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='Catálogo de endpoints disponibles para las API Keys'
        """)
        
        # 5. Insertar endpoints disponibles
        logger.info("   📝 Insertando endpoints disponibles...")
        cursor.execute("""
            INSERT INTO API_Endpoints_Disponibles (endpoint_key, endpoint_path, descripcion) VALUES
            ('get_vacancies', '/public-api/v1/vacancies', 'Obtener lista de vacantes activas del tenant'),
            ('create_candidate', '/public-api/v1/candidates', 'Registrar nuevo candidato con CV en el sistema')
            ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion)
        """)
        
        # 6. Crear procedimientos almacenados
        logger.info("   🔧 Creando procedimientos almacenados...")
        
        # Procedimiento para limpiar logs antiguos
        cursor.execute("DROP PROCEDURE IF EXISTS cleanup_api_logs")
        cursor.execute("""
            CREATE PROCEDURE cleanup_api_logs(IN dias_antiguedad INT)
            BEGIN
                DELETE FROM API_Key_Logs 
                WHERE timestamp < DATE_SUB(NOW(), INTERVAL dias_antiguedad DAY);
                
                DELETE FROM API_Key_Rate_Limits 
                WHERE ventana_inicio < DATE_SUB(NOW(), INTERVAL 7 DAY);
            END
        """)
        
        # Procedimiento para obtener estadísticas
        cursor.execute("DROP PROCEDURE IF EXISTS get_api_key_stats")
        cursor.execute("""
            CREATE PROCEDURE get_api_key_stats(IN p_api_key_id INT)
            BEGIN
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN exitoso = 1 THEN 1 ELSE 0 END) as requests_exitosos,
                    SUM(CASE WHEN exitoso = 0 THEN 1 ELSE 0 END) as requests_fallidos,
                    AVG(response_time_ms) as avg_response_time,
                    MAX(timestamp) as ultimo_uso
                FROM API_Key_Logs
                WHERE api_key_id = p_api_key_id;
            END
        """)
        
        # 7. Crear índices adicionales
        logger.info("   🔍 Creando índices adicionales...")
        try:
            cursor.execute("""
                CREATE INDEX idx_tenant_activa_expiracion 
                ON Tenant_API_Keys(tenant_id, activa, fecha_expiracion)
            """)
        except mysql.connector.Error as e:
            if e.errno != 1061:  # Error 1061 = índice duplicado
                raise
        
        try:
            cursor.execute("""
                CREATE INDEX idx_logs_fecha_tenant 
                ON API_Key_Logs(tenant_id, timestamp DESC)
            """)
        except mysql.connector.Error as e:
            if e.errno != 1061:
                raise
        
        conn.commit()
        cursor.close()
        
        logger.info("   ✅ Sistema de API Keys creado exitosamente")
    
    def _migration_002_fix_api_key_size(self, conn):
        """
        Migración 002: Aumentar tamaño de columna api_key
        La columna api_key era VARCHAR(64) pero las keys generadas necesitan más espacio
        """
        cursor = conn.cursor()
        
        logger.info("   📏 Aumentando tamaño de columna api_key...")
        
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
              AND TABLE_NAME = 'Tenant_API_Keys'
        """)
        
        if cursor.fetchone() is None:
            logger.warning("   ⚠️  Tabla Tenant_API_Keys no existe, omitiendo migración")
            cursor.close()
            return
        
        # Aumentar el tamaño de la columna api_key
        cursor.execute("""
            ALTER TABLE Tenant_API_Keys 
            MODIFY COLUMN api_key VARCHAR(255) NOT NULL
        """)
        
        # Verificar el cambio
        cursor.execute("""
            SELECT CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'Tenant_API_Keys' 
              AND COLUMN_NAME = 'api_key'
              AND TABLE_SCHEMA = DATABASE()
        """)
        
        result = cursor.fetchone()
        new_size = result[0] if result else 0
        
        logger.info(f"   ✅ Columna api_key actualizada a VARCHAR({new_size})")
        
        conn.commit()
        cursor.close()


    def _migration_004_seed_role_permissions(self, conn):
        """
        Migración 004: Insertar/actualizar JSON de permisos por pestañas en Roles.permisos
        para los roles base: Administrador, Supervisor, Reclutador.
        """
        import json
        cursor = conn.cursor()

        admin_perms = {
            "candidates": {"access": True, "scope": "all", "actions": {"create": True, "apply": True, "write": True, "full": True}, "ui": {"candidate_modal_tabs": {"summary": True, "experience": True, "applications": True, "conversations": True, "edit": True, "timeline": True}}, "redact_fields": []},
            "vacancies": {"access": True, "scope": "all", "actions": {"create": True, "write": True, "full": True}, "ui": {"hide_client_info": False, "hide_stats": False, "hide_applications_tab": False, "applications_scope": "all"}},
            "applications": {"access": True, "scope": "all", "actions": {"create": True, "write": True, "full": True}},
            "interviews": {"access": True, "scope": "all", "actions": {"create": True, "write": True}},
            "clients": {"access": True, "scope": "all", "actions": {"create": True, "write": True, "full": True}, "redact_fields": []},
            "hired": {"access": True, "scope": "all", "actions": {"create": True, "write": True, "full": True}},
            "dashboard": {"access": True},
            "conversations": {"access": True},
            "analytics": {"access": True},
            "email": {"access": True},
            "calendar": {"access": True},
            "users": {"access": True, "actions": {"manage": True}},
            "settings": {"access": True}
        }

        supervisor_perms = {
            "candidates": {"access": True, "scope": "team", "actions": {"create": True, "apply": True, "write": True, "full": False}, "ui": {"candidate_modal_tabs": {"summary": True, "experience": True, "applications": True, "conversations": True, "edit": True, "timeline": True}}, "redact_fields": []},
            "vacancies": {"access": True, "scope": "team", "actions": {"create": False, "write": True, "full": False}, "ui": {"hide_client_info": False, "hide_stats": False, "hide_applications_tab": False, "applications_scope": "all"}},
            "applications": {"access": True, "scope": "team", "actions": {"create": True, "write": True}},
            "interviews": {"access": True, "scope": "team", "actions": {"create": True, "write": True}},
            "clients": {"access": True, "scope": "team", "actions": {"create": False, "write": True}, "redact_fields": []},
            "hired": {"access": True, "scope": "team", "actions": {"create": False, "write": True}},
            "dashboard": {"access": True},
            "conversations": {"access": True},
            "analytics": {"access": True},
            "email": {"access": True},
            "calendar": {"access": True},
            "users": {"access": False, "actions": {"manage": False}},
            "settings": {"access": False}
        }

        recruiter_perms = {
            "candidates": {"access": True, "scope": "own", "actions": {"create": True, "apply": True, "write": True, "full": False}, "ui": {"candidate_modal_tabs": {"summary": True, "experience": True, "applications": False, "conversations": False, "edit": False, "timeline": False}}, "redact_fields": ["email", "telefono"]},
            "vacancies": {"access": True, "scope": "own", "actions": {"create": False, "write": False, "full": False}, "ui": {"hide_client_info": True, "hide_stats": True, "hide_applications_tab": True, "applications_scope": "own"}},
            "applications": {"access": True, "scope": "own", "actions": {"create": True, "write": False}},
            "interviews": {"access": True, "scope": "own", "actions": {"create": True, "write": False}},
            "clients": {"access": True, "scope": "own", "actions": {"create": False, "write": False}, "redact_fields": ["empresa"]},
            "hired": {"access": True, "scope": "own", "actions": {"create": False, "write": False}},
            "dashboard": {"access": True},
            "conversations": {"access": True},
            "analytics": {"access": False},
            "email": {"access": False},
            "calendar": {"access": True},
            "users": {"access": False, "actions": {"manage": False}},
            "settings": {"access": False}
        }

        role_map = {
            'Administrador': admin_perms,
            'Supervisor': supervisor_perms,
            'Reclutador': recruiter_perms
        }

        for role_name, perms in role_map.items():
            payload = json.dumps(perms, ensure_ascii=False)
            cursor.execute(
                """
                UPDATE Roles
                SET permisos = %s
                WHERE nombre = %s
                """,
                (payload, role_name)
            )

        conn.commit()
        cursor.close()
        logger.info("   ✅ Roles.permisos poblado para Administrador, Supervisor y Reclutador")

    def _migration_005_create_whatsapp_web_sessions(self, conn):
        """
        Migración 005: Crear tabla WhatsApp_Web_Sessions
        """
        cursor = conn.cursor()
        
        logger.info("   📦 Creando tabla WhatsApp_Web_Sessions...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS WhatsApp_Web_Sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tenant_id INT NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'initializing',
                qr_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                UNIQUE KEY unique_session (tenant_id, session_id),
                INDEX idx_status (status),
                FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        conn.commit()
        cursor.close()
        logger.info("   ✅ Tabla WhatsApp_Web_Sessions creada exitosamente")

    def _migration_006_agent_sessions(self, conn):
        """
        Migración 006: Sistema de Persistencia de Chat para Agentes (IDE UX)
        Crea las tablas necesarias para el historial centralizado y multi-dispositivo
        """
        cursor = conn.cursor()
        
        logger.info("   📦 Creando tablas de persistencia de Agentes...")
        
        # 1. Tabla de Sesiones (Conversaciones)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AgentSessions (
                id_session VARCHAR(255) PRIMARY KEY COMMENT 'ID único de la conversación (UUID)',
                tenant_id INT NOT NULL COMMENT 'ID del Tenant (Aislamiento)',
                user_id INT NOT NULL COMMENT 'ID del Usuario dueño del chat',
                
                titulo VARCHAR(255) DEFAULT 'Nueva Conversación' COMMENT 'Nombre visible en el historial',
                tipo ENUM('admin', 'user') DEFAULT 'user' COMMENT 'Tipo de conversación',
                
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                ultima_actividad DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_tenant_user (tenant_id, user_id),
                INDEX idx_ultima_actividad (ultima_actividad),
                
                FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='Sesiones de chat individuales para el historial tipo IDE'
        """)
        
        # 2. Tabla de Mensajes (Historial detallado)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AgentMessages (
                id_mensaje BIGINT AUTO_INCREMENT PRIMARY KEY,
                id_session VARCHAR(255) NOT NULL,
                tenant_id INT NOT NULL COMMENT 'Para filtrado rápido sin JOIN',
                
                rol ENUM('user', 'assistant', 'system') NOT NULL,
                contenido LONGTEXT NOT NULL,
                
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_session_date (id_session, fecha),
                INDEX idx_tenant_msg (tenant_id),
                
                FOREIGN KEY (id_session) REFERENCES AgentSessions(id_session) ON DELETE CASCADE,
                FOREIGN KEY (tenant_id) REFERENCES Tenants(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='Historial de mensajes centralizado para acceso multi-dispositivo'
        """)
        
        conn.commit()
        cursor.close()
        logger.info("   ✅ Tablas AgentSessions y AgentMessages creadas exitosamente")

# Función helper para ejecutar migraciones desde app.py
def run_database_migrations(db_config):
    """
    Ejecutar migraciones de base de datos
    
    Args:
        db_config: Diccionario con configuración de la BD
        
    Returns:
        bool: True si las migraciones fueron exitosas
    """
    try:
        migrations = DatabaseMigrations(db_config)
        return migrations.run_pending_migrations()
    except Exception as e:
        logger.error(f"Error ejecutando migraciones: {str(e)}")
        return False
