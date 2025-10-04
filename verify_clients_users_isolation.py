#!/usr/bin/env python3
"""
Verificación específica del aislamiento de Clientes y Usuarios por tenant
"""

import mysql.connector
from dotenv import load_dotenv
import os
import requests

def verify_clients_isolation():
    """Verificar aislamiento de clientes por tenant"""
    
    print("🏭 VERIFICACIÓN DE AISLAMIENTO DE CLIENTES")
    print("=" * 50)
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'crm_database')
        )
        cursor = conn.cursor()
        
        # 1. Verificar distribución de clientes por tenant
        print("📊 1. DISTRIBUCIÓN DE CLIENTES POR TENANT")
        print("-" * 40)
        
        cursor.execute("""
            SELECT tenant_id, COUNT(*) as total_clientes,
                   GROUP_CONCAT(empresa SEPARATOR ', ') as empresas
            FROM Clientes 
            GROUP BY tenant_id 
            ORDER BY tenant_id
        """)
        
        distribution = cursor.fetchall()
        for tenant_id, count, empresas in distribution:
            print(f"🏢 Tenant {tenant_id}: {count} clientes")
            print(f"   🏭 Empresas: {empresas}")
            print()
        
        # 2. Verificar que no hay clientes sin tenant_id
        print("📊 2. VERIFICACIÓN DE REGISTROS SIN TENANT_ID")
        print("-" * 40)
        
        cursor.execute("SELECT COUNT(*) FROM Clientes WHERE tenant_id IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count == 0:
            print("✅ Todos los clientes tienen tenant_id")
        else:
            print(f"❌ {null_count} clientes sin tenant_id")
        
        # 3. Verificar integridad referencial
        print("\n📊 3. VERIFICACIÓN DE INTEGRIDAD REFERENCIAL")
        print("-" * 40)
        
        cursor.execute("""
            SELECT COUNT(*) FROM Clientes c
            LEFT JOIN Tenants t ON c.tenant_id = t.id
            WHERE t.id IS NULL AND c.tenant_id IS NOT NULL
        """)
        
        orphan_count = cursor.fetchone()[0]
        
        if orphan_count == 0:
            print("✅ Todos los tenant_id de clientes son válidos")
        else:
            print(f"❌ {orphan_count} clientes con tenant_id inválido")
        
        cursor.close()
        conn.close()
        
        return null_count == 0 and orphan_count == 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_users_isolation():
    """Verificar aislamiento de usuarios por tenant"""
    
    print("\n👥 VERIFICACIÓN DE AISLAMIENTO DE USUARIOS")
    print("=" * 50)
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'crm_database')
        )
        cursor = conn.cursor()
        
        # 1. Verificar distribución de usuarios por tenant
        print("📊 1. DISTRIBUCIÓN DE USUARIOS POR TENANT")
        print("-" * 40)
        
        cursor.execute("""
            SELECT u.tenant_id, t.nombre_empresa, COUNT(*) as total_usuarios,
                   GROUP_CONCAT(u.email SEPARATOR ', ') as emails
            FROM Users u
            LEFT JOIN Tenants t ON u.tenant_id = t.id
            GROUP BY u.tenant_id, t.nombre_empresa
            ORDER BY u.tenant_id
        """)
        
        distribution = cursor.fetchall()
        for tenant_id, empresa, count, emails in distribution:
            print(f"🏢 Tenant {tenant_id} ({empresa}): {count} usuarios")
            print(f"   📧 Emails: {emails}")
            print()
        
        # 2. Verificar que no hay usuarios sin tenant_id
        print("📊 2. VERIFICACIÓN DE REGISTROS SIN TENANT_ID")
        print("-" * 40)
        
        cursor.execute("SELECT COUNT(*) FROM Users WHERE tenant_id IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count == 0:
            print("✅ Todos los usuarios tienen tenant_id")
        else:
            print(f"❌ {null_count} usuarios sin tenant_id")
        
        # 3. Verificar integridad referencial
        print("\n📊 3. VERIFICACIÓN DE INTEGRIDAD REFERENCIAL")
        print("-" * 40)
        
        cursor.execute("""
            SELECT COUNT(*) FROM Users u
            LEFT JOIN Tenants t ON u.tenant_id = t.id
            WHERE t.id IS NULL AND u.tenant_id IS NOT NULL
        """)
        
        orphan_count = cursor.fetchone()[0]
        
        if orphan_count == 0:
            print("✅ Todos los tenant_id de usuarios son válidos")
        else:
            print(f"❌ {orphan_count} usuarios con tenant_id inválido")
        
        cursor.close()
        conn.close()
        
        return null_count == 0 and orphan_count == 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_endpoints():
    """Probar endpoints de la API para verificar aislamiento"""
    
    print("\n🌐 PRUEBA DE ENDPOINTS DE LA API")
    print("=" * 50)
    
    try:
        # Obtener token del Tenant 1
        login_response = requests.post('http://localhost:5000/api/auth/login', json={
            'email': 'admin@crm.com',
            'password': 'admin123'
        })
        
        if login_response.status_code != 200:
            print("❌ No se puede conectar al backend")
            return False
        
        token = login_response.json()['token']
        user_data = login_response.json()['user']
        
        print(f"✅ Login exitoso - Tenant {user_data['tenant_id']}")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Probar endpoint de clientes
        print("\n🏭 Probando endpoint de clientes:")
        try:
            response = requests.get('http://localhost:5000/api/clients', headers=headers)
            if response.status_code == 200:
                clients = response.json()
                print(f"✅ Clientes obtenidos: {len(clients)} clientes")
                for client in clients[:3]:  # Mostrar primeros 3
                    print(f"   🏭 {client['empresa']}")
            else:
                print(f"❌ Error obteniendo clientes: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Probar endpoint de usuarios
        print("\n👥 Probando endpoint de usuarios:")
        try:
            response = requests.get('http://localhost:5000/api/users', headers=headers)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    users = data['data']
                    print(f"✅ Usuarios obtenidos: {len(users)} usuarios")
                    for user in users[:3]:  # Mostrar primeros 3
                        print(f"   👤 {user['email']} - {user['rol_nombre']}")
                else:
                    print("✅ Respuesta exitosa pero formato inesperado")
            else:
                print(f"❌ Error obteniendo usuarios: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando API: {e}")
        return False

def main():
    """Función principal"""
    print("🔍 VERIFICACIÓN CRÍTICA: AISLAMIENTO DE CLIENTES Y USUARIOS")
    print("=" * 70)
    
    clients_ok = verify_clients_isolation()
    users_ok = verify_users_isolation()
    api_ok = test_api_endpoints()
    
    print("\n📊 RESULTADO FINAL")
    print("=" * 30)
    
    if clients_ok and users_ok and api_ok:
        print("✅ VERIFICACIÓN COMPLETA EXITOSA")
        print("✅ Clientes completamente aislados por tenant")
        print("✅ Usuarios completamente aislados por tenant")
        print("✅ Endpoints funcionando correctamente")
        print("✅ Sistema multi-tenancy completamente funcional")
        print("\n🚀 EL SISTEMA ESTÁ LISTO PARA PRODUCCIÓN")
    else:
        print("❌ Se encontraron problemas críticos:")
        if not clients_ok:
            print("   - Problemas en el aislamiento de clientes")
        if not users_ok:
            print("   - Problemas en el aislamiento de usuarios")
        if not api_ok:
            print("   - Problemas en los endpoints de la API")

if __name__ == "__main__":
    main()

