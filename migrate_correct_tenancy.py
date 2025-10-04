#!/usr/bin/env python3
"""
Script para migrar a la arquitectura correcta de multi-tenancy
TENANTS = Empresas de reclutamiento (usuarios del sistema)
CLIENTES = Empresas que buscan personal (clientes de los tenants)
"""

import mysql.connector
from dotenv import load_dotenv
import os
import uuid
import json

load_dotenv()

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'crm_database')
        )
    except Exception as e:
        print(f"Error conectando a BD: {e}")
        return None

def create_tenants_structure():
    """Crear estructura de tenants correcta"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        print("🏗️ Creando estructura de Tenants...")
        
        # 1. Crear tabla Tenants
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
        
        # 2. Crear tabla Tenant_Roles
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
        print("✅ Estructura de Tenants creada")
        return True
        
    except Exception as e:
        print(f"❌ Error creando estructura: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def migrate_existing_users():
    """Migrar usuarios existentes a la nueva estructura"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        print("🔄 Migrando usuarios existentes...")
        
        # 1. Obtener tenants únicos de usuarios existentes
        cursor.execute("SELECT DISTINCT tenant_id FROM Users WHERE tenant_id IS NOT NULL")
        existing_tenants = cursor.fetchall()
        
        # 2. Crear tenants en la nueva tabla
        for tenant_id_tuple in existing_tenants:
            tenant_id = tenant_id_tuple[0]
            
            # Verificar si el tenant ya existe
            cursor.execute("SELECT id_tenant FROM Tenants WHERE id_tenant = %s", (tenant_id,))
            if cursor.fetchone():
                print(f"✅ Tenant {tenant_id} ya existe")
                continue
            
            # Crear tenant
            cursor.execute("""
                INSERT INTO Tenants (id_tenant, nombre_empresa, email_contacto, plan, api_key, activo)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                tenant_id,
                f"Agencia de Reclutamiento {tenant_id}",
                f"admin@agencia{tenant_id}.com",
                "basic",
                str(uuid.uuid4()),
                True
            ))
            
            print(f"✅ Tenant {tenant_id} creado")
        
        # 3. Crear roles por defecto para cada tenant
        cursor.execute("SELECT id_tenant FROM Tenants")
        tenants = cursor.fetchall()
        
        for tenant in tenants:
            tenant_id = tenant[0]
            
            # Crear roles por defecto
            roles = [
                ("ADMIN_EMPRESA", "Administrador de la empresa", {
                    "usuarios": True, "candidatos": True, "vacantes": True, 
                    "postulaciones": True, "reportes": True, "configuracion": True
                }),
                ("RECLUTADOR", "Reclutador de la empresa", {
                    "candidatos": True, "vacantes": True, "postulaciones": True, 
                    "reportes": False, "configuracion": False
                }),
                ("VISUALIZADOR", "Solo lectura", {
                    "candidatos": False, "vacantes": False, "postulaciones": False,
                    "reportes": False, "configuracion": False, "read_only": True
                })
            ]
            
            for rol_name, desc, permisos in roles:
                cursor.execute("""
                    INSERT INTO Tenant_Roles (tenant_id, nombre_rol, descripcion, permisos)
                    VALUES (%s, %s, %s, %s)
                """, (tenant_id, rol_name, desc, json.dumps(permisos)))
            
            print(f"✅ Roles creados para tenant {tenant_id}")
        
        conn.commit()
        print("✅ Migración de usuarios completada")
        return True
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def fix_users_table():
    """Corregir tabla Users para usar tenant_id correctamente"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        print("🔧 Corrigiendo tabla Users...")
        
        # Eliminar columna id_cliente de Users (solo debe estar en Vacantes)
        try:
            cursor.execute("ALTER TABLE Users DROP COLUMN id_cliente")
            print("✅ Columna id_cliente eliminada de Users")
        except Exception as e:
            print(f"ℹ️ Columna id_cliente no existía o ya fue eliminada: {e}")
        
        # Asegurar que Users tenga tenant_id
        try:
            cursor.execute("ALTER TABLE Users ADD COLUMN tenant_id INT")
            print("✅ Columna tenant_id agregada a Users")
        except Exception as e:
            print(f"ℹ️ Columna tenant_id ya existe: {e}")
        
        # Agregar foreign key constraint
        try:
            cursor.execute("ALTER TABLE Users ADD FOREIGN KEY (tenant_id) REFERENCES Tenants(id_tenant)")
            print("✅ Foreign key constraint agregado")
        except Exception as e:
            print(f"ℹ️ Foreign key constraint ya existe: {e}")
        
        conn.commit()
        print("✅ Tabla Users corregida")
        return True
        
    except Exception as e:
        print(f"❌ Error corrigiendo Users: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def create_indexes():
    """Crear índices para mejor rendimiento"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        print("📊 Creando índices...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_tenant ON Users(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_afiliados_tenant ON Afiliados(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_vacantes_tenant ON Vacantes(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_postulaciones_tenant ON Postulaciones(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_tags_tenant ON Tags(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_email_templates_tenant ON Email_Templates(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_whatsapp_templates_tenant ON Whatsapp_Templates(tenant_id)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"✅ Índice creado: {index_sql.split('idx_')[1].split(' ON')[0]}")
            except Exception as e:
                print(f"ℹ️ Índice ya existe o error: {e}")
        
        conn.commit()
        print("✅ Índices creados")
        return True
        
    except Exception as e:
        print(f"❌ Error creando índices: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_migration():
    """Verificar que la migración fue exitosa"""
    conn = get_db_connection()
    if not conn:
        return
    
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
        
        # Verificar usuarios
        cursor.execute("SELECT COUNT(*) FROM Users")
        user_count = cursor.fetchone()[0]
        print(f"📊 Usuarios totales: {user_count}")
        
        # Mostrar estructura
        cursor.execute("SELECT id_tenant, nombre_empresa, plan FROM Tenants")
        tenants = cursor.fetchall()
        print("\n🏢 TENANTS CREADOS:")
        for tenant in tenants:
            print(f"  - ID: {tenant[0]}, Empresa: {tenant[1]}, Plan: {tenant[2]}")
        
        # Verificar usuarios por tenant
        cursor.execute("""
            SELECT u.tenant_id, t.nombre_empresa, COUNT(*) as usuarios
            FROM Users u
            LEFT JOIN Tenants t ON u.tenant_id = t.id_tenant
            GROUP BY u.tenant_id, t.nombre_empresa
        """)
        user_dist = cursor.fetchall()
        print("\n👥 USUARIOS POR TENANT:")
        for dist in user_dist:
            print(f"  - Tenant {dist[0]} ({dist[1]}): {dist[2]} usuarios")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando: {e}")

def show_architecture_explanation():
    """Mostrar explicación de la nueva arquitectura"""
    print("\n" + "="*60)
    print("🏗️ ARQUITECTURA CORRECTA IMPLEMENTADA")
    print("="*60)
    print()
    print("📋 TENANTS (Empresas de reclutamiento):")
    print("  • Son las empresas que usan el sistema")
    print("  • Cada tenant tiene sus propios usuarios")
    print("  • Aislamiento completo de datos")
    print()
    print("🏢 CLIENTES (Empresas que buscan personal):")
    print("  • Son las empresas que buscan personal")
    print("  • Se vinculan a vacantes específicas")
    print("  • Un tenant puede tener múltiples clientes")
    print()
    print("👥 USUARIOS (Personal de los tenants):")
    print("  • Pertenecen a un tenant específico")
    print("  • No tienen relación directa con clientes")
    print("  • Roles: ADMIN_EMPRESA, RECLUTADOR, VISUALIZADOR")
    print()
    print("💼 VACANTES:")
    print("  • Pertenecen a un tenant (quien las gestiona)")
    print("  • Se vinculan a un cliente (quien busca personal)")
    print("  • Filtro: tenant_id para aislamiento")
    print()
    print("="*60)

if __name__ == "__main__":
    print("🚀 INICIANDO MIGRACIÓN A ARQUITECTURA CORRECTA")
    print("="*60)
    
    success = True
    
    if not create_tenants_structure():
        success = False
    
    if not migrate_existing_users():
        success = False
    
    if not fix_users_table():
        success = False
    
    if not create_indexes():
        success = False
    
    if success:
        verify_migration()
        show_architecture_explanation()
        print("\n✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    else:
        print("\n❌ MIGRACIÓN FALLÓ - REVISAR ERRORES")
    
    print("="*60)
