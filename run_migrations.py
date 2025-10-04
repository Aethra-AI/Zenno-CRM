#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        self.connection = None
        self.migrations_dir = Path(__file__).parent / 'migrations'
        self.migrations_table = "schema_migrations"
        
    def get_connection(self):
        """Establece conexión a la base de datos"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=int(os.getenv('DB_PORT', '3306')),
                database=os.getenv('DB_NAME')
            )
            return self.connection
        except Error as e:
            logger.error(f"Error al conectar a la base de datos: {e}")
            raise
    
    def close_connection(self):
        """Cierra la conexión a la base de datos"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Conexión a la base de datos cerrada")
    
    def ensure_migrations_table(self):
        """Asegura que exista la tabla de control de migraciones"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    version VARCHAR(50) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_version (version)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            self.connection.commit()
            logger.info("Tabla de migraciones verificada/creada")
        except Error as e:
            logger.error(f"Error al crear la tabla de migraciones: {e}")
            raise
    
    def get_applied_migrations(self):
        """Obtiene la lista de migraciones ya aplicadas"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(f"SELECT version FROM {self.migrations_table} ORDER BY version")
            return [row['version'] for row in cursor.fetchall()]
        except Error as e:
            logger.error(f"Error al obtener migraciones aplicadas: {e}")
            return []
    
    def get_pending_migrations(self, applied_migrations):
        """Obtiene la lista de migraciones pendientes"""
        if not self.migrations_dir.exists():
            logger.error(f"Directorio de migraciones no encontrado: {self.migrations_dir}")
            return []
            
        all_migrations = sorted([f for f in os.listdir(self.migrations_dir) 
                               if f.endswith('.sql')])
        
        return [m for m in all_migrations 
                if m.split('_', 1)[0] not in applied_migrations]
    
    def apply_migration(self, migration_file):
        """Aplica una migración específica"""
        migration_path = self.migrations_dir / migration_file
        if not migration_path.exists():
            logger.error(f"Archivo de migración no encontrado: {migration_path}")
            return False
        
        version = migration_file.split('_', 1)[0]
        name = migration_file.split('_', 1)[1].rsplit('.', 1)[0]
        
        try:
            with open(migration_path, 'r', encoding='utf-8') as f:
                sql_commands = f.read()
                
            # Dividir los comandos SQL por punto y coma
            commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
            
            cursor = self.connection.cursor()
            
            # Ejecutar cada comando por separado
            for command in commands:
                if command:  # Asegurarse de que el comando no esté vacío
                    cursor.execute(command)
            
            # Registrar la migración como aplicada
            cursor.execute(
                f"""
                INSERT INTO {self.migrations_table} (version, name, applied_at)
                VALUES (%s, %s, NOW())
                """,
                (version, name)
            )
            
            self.connection.commit()
            logger.info(f"Migración aplicada exitosamente: {migration_file}")
            return True
            
        except Error as e:
            self.connection.rollback()
            logger.error(f"Error al aplicar la migración {migration_file}: {e}")
            return False
    
    def run_migrations(self):
        """Ejecuta todas las migraciones pendientes"""
        try:
            self.get_connection()
            self.ensure_migrations_table()
            
            applied = self.get_applied_migrations()
            logger.info(f"Migraciones aplicadas: {len(applied)}")
            
            pending = self.get_pending_migrations(applied)
            logger.info(f"Migraciones pendientes: {len(pending)}")
            
            if not pending:
                logger.info("No hay migraciones pendientes por aplicar.")
                return True
                
            logger.info("Aplicando migraciones pendientes...")
            
            for migration in pending:
                logger.info(f"Aplicando migración: {migration}")
                if not self.apply_migration(migration):
                    logger.error(f"Error al aplicar la migración: {migration}")
                    return False
                    
            logger.info("Todas las migraciones se aplicaron exitosamente.")
            return True
            
        except Exception as e:
            logger.error(f"Error durante la migración: {e}")
            return False
            
        finally:
            self.close_connection()

if __name__ == "__main__":
    logger.info("Iniciando proceso de migración...")
    
    migrator = DatabaseMigrator()
    if migrator.run_migrations():
        logger.info("Proceso de migración completado con éxito.")
    else:
        logger.error("El proceso de migración falló.")
        exit(1)
