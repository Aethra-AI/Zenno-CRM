#!/usr/bin/env python3
"""
Script para migrar a un sistema de multi-tenancy correcto
"""

import mysql.connector
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

def create_tenants_table():
    """Crear tabla de Tenants"""
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'crm_database')
    )
    cursor = conn.cursor()
    
    try:
        print("🏗️ Creando tabla Tenants...")
        
        # Crear tabla Tenants
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Tenants (
                id_tenant INT AUTO_INCREMENT PRIMARY KEY,
                nombre_empresa VARCHAR(100) NOT NULL,
                email_contacto VARCHAR(100) NOT NULL,
                telefono VARCHAR(20),
                direccion TEXT,
                plan VARCHAR(20) DEFAULT 'basic' CHECK (plan IN ('basic', 'premium', 'enterprise')),
                api_key VARCHAR(255) UNIQUE,
                activo BOOLEAN DEFAULT TRUE,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla Tenant_Roles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Tenant_Roles (
                id_rol INT AUTO_INCREMENT PRIMARY KEY,
                tenant_id INT NOT NULL,
                nombre_rol VARCHAR(50) NOT NULL,
                descripcion TEXT,
                permisos JSON,
                activo BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (tenant_id) REFERENCES Tenants(id_tenant) ON DELETE CASCADE,
                UNIQUE KEY unique_rol_tenant (tenant_id, nombre_rol)
            )
        """)
        
        conn.commit()
        print("✅ Tablas creadas exitosamente")
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
    finally:
        cursor.close()
        conn.close()

def migrate_existing_data():
    """Migrar datos existentes"""
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'crm_database')
    )
    cursor = conn.cursor()
    
    try:
        print("🔄 Migrando datos existentes...")
        
        # Obtener tenants únicos de la tabla actual
        cursor.execute("SELECT DISTINCT tenant_id FROM Users WHERE tenant_id IS NOT NULL")
        existing_tenants = cursor.fetchall()
        
        for tenant_id in existing_tenants:
            tenant_id = tenant_id[0]
            
            # Crear tenant en la nueva tabla
            cursor.execute("""
                INSERT INTO Tenants (id_tenant, nombre_empresa, email_contacto, plan, api_key, activo)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                tenant_id,
                f"Empresa {tenant_id}",
                f"admin@empresa{tenant_id}.com",
                "basic",
                str(uuid.uuid4()),
                True
            ))
            
            print(f"✅ Tenant {tenant_id} migrado")
        
        # Crear roles por defecto para cada tenant
        cursor.execute("SELECT id_tenant FROM Tenants")
        tenants = cursor.fetchall()
        
        for tenant in tenants:
            tenant_id = tenant[0]
            
            # Crear roles por defecto
            roles = [
                ("ADMIN_EMPRESA", "Administrador de la empresa", {"all": True}),
                ("RECLUTADOR", "Reclutador de la empresa", {"candidates": True, "vacancies": True}),
                ("VISUALIZADOR", "Solo lectura", {"read": True})
            ]
            
            for rol_name, desc, permisos in roles:
                cursor.execute("""
                    INSERT INTO Tenant_Roles (tenant_id, nombre_rol, descripcion, permisos)
                    VALUES (%s, %s, %s, %s)
                """, (tenant_id, rol_name, desc, str(permisos).replace("'", '"')))
            
            print(f"✅ Roles creados para tenant {tenant_id}")
        
        conn.commit()
        print("✅ Migración completada")
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def verify_migration():
    """Verificar que la migración fue exitosa"""
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'crm_database')
    )
    cursor = conn.cursor()
    
    try:
        print("🔍 Verificando migración...")
        
        # Verificar tenants
        cursor.execute("SELECT COUNT(*) FROM Tenants")
        tenant_count = cursor.fetchone()[0]
        print(f"📊 Tenants creados: {tenant_count}")
        
        # Verificar roles
        cursor.execute("SELECT COUNT(*) FROM Tenant_Roles")
        role_count = cursor.fetchone()[0]
        print(f"📊 Roles creados: {role_count}")
        
        # Mostrar estructura
        cursor.execute("SELECT id_tenant, nombre_empresa, plan FROM Tenants")
        tenants = cursor.fetchall()
        print("\n🏢 TENANTS CREADOS:")
        for tenant in tenants:
            print(f"  - ID: {tenant[0]}, Empresa: {tenant[1]}, Plan: {tenant[2]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO MIGRACIÓN A MULTI-TENANCY CORRECTO")
    print("=" * 50)
    
    create_tenants_table()
    migrate_existing_data()
    verify_migration()
    
    print("\n✅ MIGRACIÓN COMPLETADA")
    print("=" * 50)
