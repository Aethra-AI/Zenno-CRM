#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear las tablas del calendario
"""

import mysql.connector
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'zenno_crm'),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def create_calendar_tables():
    """Crear las tablas del calendario"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Crear tabla para recordatorios del calendario
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_reminders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tenant_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                date DATE NOT NULL,
                time TIME NOT NULL,
                type ENUM('personal', 'team', 'general') NOT NULL DEFAULT 'personal',
                priority ENUM('low', 'medium', 'high') NOT NULL DEFAULT 'medium',
                status ENUM('pending', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
                created_by INT NOT NULL,
                assigned_to JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_tenant_date (tenant_id, date),
                INDEX idx_tenant_type (tenant_id, type),
                INDEX idx_created_by (created_by),
                INDEX idx_status (status)
            )
        """)
        
        # Crear tabla para entrevistas (si no existe)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tenant_id INT NOT NULL,
                candidate_id INT NOT NULL,
                vacancy_id INT NOT NULL,
                interview_date DATE NOT NULL,
                interview_time TIME NOT NULL,
                status ENUM('scheduled', 'completed', 'cancelled', 'rescheduled') NOT NULL DEFAULT 'scheduled',
                notes TEXT,
                interviewer VARCHAR(255),
                created_by INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_tenant_date (tenant_id, interview_date),
                INDEX idx_candidate (candidate_id),
                INDEX idx_vacancy (vacancy_id),
                INDEX idx_status (status)
            )
        """)
        
        # Insertar algunos datos de ejemplo
        cursor.execute("""
            INSERT IGNORE INTO calendar_reminders 
            (tenant_id, title, description, date, time, type, priority, created_by, assigned_to) 
            VALUES
            (1, 'Reunión semanal de equipo', 'Revisión de objetivos y metas semanales', CURDATE(), '09:00:00', 'team', 'high', 1, JSON_ARRAY(1, 2)),
            (1, 'Seguimiento de candidatos', 'Revisar postulaciones pendientes', CURDATE() + INTERVAL 1 DAY, '14:00:00', 'personal', 'medium', 1, JSON_ARRAY(1)),
            (1, 'Capacitación de reclutamiento', 'Sesión de capacitación sobre nuevas técnicas', CURDATE() + INTERVAL 3 DAY, '10:00:00', 'general', 'medium', 1, JSON_ARRAY(1, 2, 3))
        """)
        
        # Insertar algunas entrevistas de ejemplo
        cursor.execute("""
            INSERT IGNORE INTO interviews 
            (tenant_id, candidate_id, vacancy_id, interview_date, interview_time, status, interviewer, created_by) 
            VALUES
            (1, 1, 1, CURDATE() + INTERVAL 2 DAY, '10:00:00', 'scheduled', 'Juan Pérez', 1),
            (1, 2, 2, CURDATE() + INTERVAL 3 DAY, '15:30:00', 'scheduled', 'María González', 1),
            (1, 3, 1, CURDATE() + INTERVAL 5 DAY, '11:00:00', 'scheduled', 'Carlos López', 1)
        """)
        
        conn.commit()
        print("✅ Tablas del calendario creadas exitosamente")
        print("✅ Datos de ejemplo insertados")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error creando las tablas: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("Creando tablas del calendario...")
    success = create_calendar_tables()
    if success:
        print("🎉 ¡Proceso completado exitosamente!")
    else:
        print("💥 Error en el proceso")

