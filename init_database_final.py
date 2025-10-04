#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para inicializar la base de datos completa del sistema WhatsApp multi-tenant
"""

import sqlite3
import os
import hashlib
from datetime import datetime

def create_database():
    """Crear base de datos completa"""
    db_path = os.path.join(os.path.dirname(__file__), 'whatsapp_multi_tenant.db')
    
    # Eliminar base de datos existente si existe
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ Base de datos anterior eliminada")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🏗️ Creando tablas de la base de datos...")
    
    # Tabla de tenants
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            domain TEXT UNIQUE,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            tenant_id INTEGER NOT NULL,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants (id)
        )
    """)
    
    # Tabla de configuración WhatsApp por tenant
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            mode TEXT NOT NULL DEFAULT 'web_js',
            api_token TEXT,
            phone_number_id TEXT,
            webhook_verify_token TEXT,
            business_account_id TEXT,
            status TEXT DEFAULT 'inactive',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants (id),
            UNIQUE(tenant_id)
        )
    """)
    
    # Tabla de sesiones WhatsApp Web
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_web_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'initializing',
            qr_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(tenant_id, session_id)
        )
    """)
    
    # Tabla de conversaciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            phone_number TEXT NOT NULL,
            contact_name TEXT,
            last_message TEXT,
            last_message_time TIMESTAMP,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants (id),
            UNIQUE(tenant_id, phone_number)
        )
    """)
    
    # Tabla de mensajes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            conversation_id INTEGER NOT NULL,
            message_id TEXT UNIQUE NOT NULL,
            from_number TEXT NOT NULL,
            to_number TEXT NOT NULL,
            message_type TEXT NOT NULL,
            content TEXT,
            media_url TEXT,
            status TEXT DEFAULT 'sent',
            direction TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants (id),
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    """)
    
    # Tabla de plantillas de mensajes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            subject TEXT,
            content TEXT NOT NULL,
            variables TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_default BOOLEAN DEFAULT 0,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    """)
    
    print("✅ Tablas creadas exitosamente")
    
    # Insertar datos iniciales
    print("📝 Insertando datos iniciales...")
    
    # Crear tenant por defecto
    cursor.execute("""
        INSERT INTO tenants (id, name, domain, status)
        VALUES (1, 'Tenant Principal', 'localhost', 'active')
    """)
    
    # Crear usuario admin
    password_hash = hashlib.md5("admin123".encode()).hexdigest()
    cursor.execute("""
        INSERT INTO users (email, username, password, tenant_id, role, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("admin@example.com", "admin", password_hash, 1, "admin", "active"))
    
    # Crear configuración WhatsApp por defecto
    cursor.execute("""
        INSERT INTO whatsapp_configs (tenant_id, mode, status)
        VALUES (1, 'web_js', 'active')
    """)
    
    # Crear conversación de prueba
    cursor.execute("""
        INSERT INTO conversations (tenant_id, phone_number, contact_name, last_message, last_message_time, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, "1234567890", "Contacto Prueba", "Mensaje de prueba", datetime.now(), "active"))
    
    # Crear plantilla de mensaje por defecto
    cursor.execute("""
        INSERT INTO message_templates (tenant_id, name, category, content, created_by)
        VALUES (?, ?, ?, ?, ?)
    """, (1, "Saludo", "UTILITY", "Hola {nombre}, gracias por contactarnos.", 1))
    
    conn.commit()
    conn.close()
    
    print("✅ Base de datos inicializada exitosamente")
    print(f"📁 Ubicación: {db_path}")
    print("\n🔑 Credenciales por defecto:")
    print("   Email: admin@example.com")
    print("   Username: admin")
    print("   Password: admin123")
    print("   Tenant ID: 1")

if __name__ == "__main__":
    create_database()
