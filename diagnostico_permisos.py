#!/usr/bin/env python3
"""
🔍 DIAGNÓSTICO DE PERMISOS
Script para identificar por qué los filtros no funcionan
"""

import mysql.connector
from mysql.connector import Error
import json

# CONFIGURACIÓN - Cambiar según tu entorno
DB_CONFIG = {
    'host': 'localhost',
    'database': 'crm_db',  # Cambiar al nombre de tu BD
    'user': 'root',         # Cambiar al usuario de tu BD
    'password': 'tu_password'  # Cambiar a tu contraseña
}

def test_connection():
    """Probar conexión a la BD"""
    print("=" * 60)
    print("🔌 PROBANDO CONEXIÓN A LA BASE DE DATOS")
    print("=" * 60)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print("✅ Conexión exitosa")
            db_info = conn.get_server_info()
            print(f"📊 MySQL version: {db_info}")
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()[0]
            print(f"📁 Base de datos: {db_name}")
            cursor.close()
            conn.close()
            return True
    except Error as e:
        print(f"❌ Error de conexión: {e}")
        return False

def check_roles():
    """Verificar roles en la BD"""
    print("\n" + "=" * 60)
    print("👥 VERIFICANDO ROLES")
    print("=" * 60)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                id,
                nombre,
                activo,
                LENGTH(nombre) as longitud,
                HEX(nombre) as hex_nombre
            FROM Roles
            ORDER BY id
        """)
        
        roles = cursor.fetchall()
        
        print(f"\n📋 Total de roles: {len(roles)}\n")
        
        for role in roles:
            print(f"ID: {role['id']}")
            print(f"Nombre: '{role['nombre']}'")
            print(f"Longitud: {role['longitud']} caracteres")
            print(f"Activo: {'✅' if role['activo'] else '❌'}")
            print(f"HEX: {role['hex_nombre']}")
            
            # Pruebas de comparación
            if role['nombre'] == 'Administrador':
                print("✅ Match exacto: 'Administrador'")
            elif 'Administrador' in role['nombre']:
                print("⚠️  Contiene 'Administrador' pero no es exacto")
            
            if role['nombre'] == 'Supervisor':
                print("✅ Match exacto: 'Supervisor'")
            elif 'Supervisor' in role['nombre']:
                print("⚠️  Contiene 'Supervisor' pero no es exacto")
            
            if role['nombre'] == 'Reclutador':
                print("✅ Match exacto: 'Reclutador'")
            elif 'Reclutador' in role['nombre']:
                print("⚠️  Contiene 'Reclutador' pero no es exacto")
            
            print("-" * 40)
        
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"❌ Error: {e}")
        return False

def check_users(tenant_id=1):
    """Verificar usuarios y sus roles"""
    print("\n" + "=" * 60)
    print(f"👤 VERIFICANDO USUARIOS (Tenant {tenant_id})")
    print("=" * 60)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                u.id,
                u.nombre,
                u.email,
                u.rol_id,
                r.nombre as rol_nombre,
                u.tenant_id,
                u.activo as user_activo,
                r.activo as rol_activo,
                CASE 
                    WHEN r.nombre = 'Administrador' THEN 'Admin'
                    WHEN r.nombre = 'Supervisor' THEN 'Supervisor'
                    WHEN r.nombre = 'Reclutador' THEN 'Reclutador'
                    ELSE 'Desconocido'
                END as rol_detectado
            FROM Users u
            LEFT JOIN Roles r ON u.rol_id = r.id
            WHERE u.tenant_id = %s
            ORDER BY u.id
        """, (tenant_id,))
        
        users = cursor.fetchall()
        
        print(f"\n📋 Total de usuarios: {len(users)}\n")
        
        admin_count = 0
        supervisor_count = 0
        recruiter_count = 0
        unknown_count = 0
        
        for user in users:
            print(f"ID: {user['id']}")
            print(f"Nombre: {user['nombre']}")
            print(f"Email: {user['email']}")
            print(f"Rol ID: {user['rol_id']}")
            print(f"Rol Nombre: '{user['rol_nombre']}'")
            print(f"Rol Detectado: {user['rol_detectado']}")
            print(f"User Activo: {'✅' if user['user_activo'] else '❌'}")
            print(f"Rol Activo: {'✅' if user['rol_activo'] else '❌'}")
            
            if user['rol_detectado'] == 'Admin':
                admin_count += 1
                print("🔐 Este usuario es ADMINISTRADOR")
            elif user['rol_detectado'] == 'Supervisor':
                supervisor_count += 1
                print("👔 Este usuario es SUPERVISOR")
            elif user['rol_detectado'] == 'Reclutador':
                recruiter_count += 1
                print("👤 Este usuario es RECLUTADOR")
            else:
                unknown_count += 1
                print("⚠️  ROL DESCONOCIDO - PROBLEMA AQUÍ")
            
            print("-" * 40)
        
        print("\n📊 RESUMEN:")
        print(f"Administradores: {admin_count}")
        print(f"Supervisores: {supervisor_count}")
        print(f"Reclutadores: {recruiter_count}")
        print(f"Desconocidos: {unknown_count}")
        
        if unknown_count > 0:
            print("\n⚠️  ADVERTENCIA: Hay usuarios con roles desconocidos")
            print("   Esto causará que los filtros no funcionen correctamente")
        
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"❌ Error: {e}")
        return False

def test_is_admin_function(user_id, tenant_id=1):
    """Simular la función is_admin de Python"""
    print("\n" + "=" * 60)
    print(f"🧪 PROBANDO FUNCIÓN is_admin(user_id={user_id}, tenant_id={tenant_id})")
    print("=" * 60)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Simular exactamente lo que hace get_user_role_info
        cursor.execute("""
            SELECT 
                r.id as role_id,
                r.nombre as role_name,
                r.permisos as permissions
            FROM Users u
            JOIN Roles r ON u.rol_id = r.id
            WHERE u.id = %s 
              AND u.tenant_id = %s 
              AND u.activo = 1
              AND r.activo = 1
        """, (user_id, tenant_id))
        
        result = cursor.fetchone()
        
        if result:
            print(f"\n✅ Usuario encontrado")
            print(f"Role ID: {result['role_id']}")
            print(f"Role Name: '{result['role_name']}'")
            
            # Simular is_admin
            is_admin = result['role_name'] == 'Administrador'
            print(f"\nComparación: '{result['role_name']}' == 'Administrador'")
            print(f"Resultado is_admin: {is_admin}")
            
            if is_admin:
                print("✅ Este usuario SÍ es detectado como Admin")
                print("   Verá TODOS los datos del tenant (sin filtros)")
            else:
                print("❌ Este usuario NO es detectado como Admin")
                print("   Verá solo datos filtrados")
            
            # Simular is_supervisor
            is_supervisor = result['role_name'] == 'Supervisor'
            print(f"\nComparación: '{result['role_name']}' == 'Supervisor'")
            print(f"Resultado is_supervisor: {is_supervisor}")
            
            # Simular is_recruiter
            is_recruiter = result['role_name'] == 'Reclutador'
            print(f"\nComparación: '{result['role_name']}' == 'Reclutador'")
            print(f"Resultado is_recruiter: {is_recruiter}")
            
        else:
            print(f"\n❌ Usuario NO encontrado o inactivo")
            print("   Posibles causas:")
            print("   - user_id o tenant_id incorrectos")
            print("   - Usuario inactivo")
            print("   - Rol inactivo")
        
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"❌ Error: {e}")
        return False

def check_team_structure(tenant_id=1):
    """Verificar estructura de equipos"""
    print("\n" + "=" * 60)
    print(f"👥 VERIFICANDO ESTRUCTURA DE EQUIPOS (Tenant {tenant_id})")
    print("=" * 60)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                ts.id,
                s.id as supervisor_id,
                s.nombre as supervisor_nombre,
                m.id as miembro_id,
                m.nombre as miembro_nombre,
                ts.is_active
            FROM Team_Structure ts
            JOIN Users s ON ts.supervisor_id = s.id
            JOIN Users m ON ts.team_member_id = m.id
            WHERE ts.tenant_id = %s
        """, (tenant_id,))
        
        teams = cursor.fetchall()
        
        if len(teams) == 0:
            print("\n📋 No hay equipos configurados")
        else:
            print(f"\n📋 Total de asignaciones: {len(teams)}\n")
            
            for team in teams:
                print(f"Supervisor: {team['supervisor_nombre']} (ID: {team['supervisor_id']})")
                print(f"Miembro: {team['miembro_nombre']} (ID: {team['miembro_id']})")
                print(f"Activo: {'✅' if team['is_active'] else '❌'}")
                print("-" * 40)
        
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "=" * 60)
    print("🔍 DIAGNÓSTICO DE PERMISOS - CRM ZENNO")
    print("=" * 60)
    
    # 1. Probar conexión
    if not test_connection():
        print("\n❌ No se pudo conectar a la base de datos")
        print("   Por favor verifica DB_CONFIG en este script")
        return
    
    # 2. Verificar roles
    if not check_roles():
        return
    
    # 3. Verificar usuarios
    tenant_id = int(input("\n📝 Ingresa el tenant_id a verificar (default 1): ") or "1")
    if not check_users(tenant_id):
        return
    
    # 4. Probar función is_admin
    user_id = input("\n📝 Ingresa el user_id a probar (o Enter para saltar): ")
    if user_id:
        test_is_admin_function(int(user_id), tenant_id)
    
    # 5. Verificar equipos
    check_team_structure(tenant_id)
    
    print("\n" + "=" * 60)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("=" * 60)
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Revisa si hay roles 'Desconocidos'")
    print("2. Verifica que los nombres de roles sean EXACTOS")
    print("3. Si hay diferencias, actualiza los nombres en la BD")
    print("4. O actualiza permission_service.py para usar los nombres correctos")
    print("\n")

if __name__ == "__main__":
    main()







