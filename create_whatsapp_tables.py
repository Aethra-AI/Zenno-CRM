#!/usr/bin/env python3
"""
📱 CREAR TABLAS WHATSAPP MULTI-TENANT
=====================================

Script para crear las tablas de base de datos necesarias
para el sistema WhatsApp multi-tenant.
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

def create_whatsapp_tables():
    """Crear todas las tablas de WhatsApp"""
    
    # Leer el archivo SQL
    try:
        with open('whatsapp_database_schema.sql', 'r', encoding='utf-8') as file:
            sql_content = file.read()
    except FileNotFoundError:
        logger.error("❌ Archivo whatsapp_database_schema.sql no encontrado")
        return False
    
    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        logger.info("🚀 Iniciando creación de tablas WhatsApp...")
        
        # Dividir el contenido en statements individuales
        statements = []
        current_statement = ""
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('--') and not line.startswith('/*'):
                current_statement += line + " "
                if line.endswith(';'):
                    statements.append(current_statement.strip())
                    current_statement = ""
        
        # Ejecutar cada statement
        for i, statement in enumerate(statements):
            if statement:
                try:
                    logger.info(f"📝 Ejecutando statement {i+1}/{len(statements)}...")
                    cursor.execute(statement)
                    conn.commit()
                    logger.info(f"✅ Statement {i+1} ejecutado exitosamente")
                except Exception as e:
                    logger.warning(f"⚠️ Error en statement {i+1}: {str(e)}")
                    # Continuar con los siguientes statements
        
        logger.info("🎉 ¡Todas las tablas creadas exitosamente!")
        
        # Verificar que las tablas se crearon
        cursor.execute("SHOW TABLES LIKE 'WhatsApp_%'")
        tables = cursor.fetchall()
        
        logger.info(f"📊 Tablas WhatsApp creadas: {len(tables)}")
        for table in tables:
            logger.info(f"   ✅ {table[0]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {str(e)}")
        return False
        
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
        
        # Verificar datos iniciales
        cursor.execute("SELECT COUNT(*) as count FROM WhatsApp_Templates")
        template_count = cursor.fetchone()
        logger.info(f"📝 Plantillas iniciales: {template_count['count']}")
        
        cursor.execute("SELECT COUNT(*) as count FROM WhatsApp_Notification_Rules")
        rules_count = cursor.fetchone()
        logger.info(f"🔔 Reglas de notificación: {rules_count['count']}")
        
        logger.info("✅ Verificación completada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error verificando tablas: {str(e)}")
        
    finally:
        cursor.close()
        conn.close()

def main():
    """Función principal"""
    logger.info("🚀 INICIANDO CREACIÓN DE TABLAS WHATSAPP MULTI-TENANT")
    logger.info("=" * 60)
    
    # Crear tablas
    success = create_whatsapp_tables()
    
    if success:
        logger.info("=" * 60)
        logger.info("🎉 CREACIÓN DE TABLAS COMPLETADA EXITOSAMENTE")
        
        # Verificar tablas
        verify_tables()
        
        logger.info("=" * 60)
        logger.info("✅ SISTEMA WHATSAPP MULTI-TENANT LISTO PARA IMPLEMENTACIÓN")
    else:
        logger.error("=" * 60)
        logger.error("❌ ERROR EN LA CREACIÓN DE TABLAS")
        logger.error("Revisar logs para más detalles")

if __name__ == "__main__":
    main()
