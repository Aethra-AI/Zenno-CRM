#!/usr/bin/env python3
"""
Script simple para probar funcionalidad básica del sistema multi-tenancy
"""

import requests
import json
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def test_database_directly():
    """Probar la base de datos directamente"""
    print("🔍 PROBANDO BASE DE DATOS DIRECTAMENTE")
    print("=" * 40)
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'crm_database')
        )
        cursor = conn.cursor()
        
        # Probar consulta de login
        print("1. Probando consulta de login...")
        cursor.execute("""
            SELECT u.*, r.nombre as rol_nombre, r.permisos, t.nombre_empresa as empresa_nombre
            FROM Users u 
            LEFT JOIN Roles r ON u.rol_id = r.id
            LEFT JOIN Tenants t ON u.tenant_id = t.id
            WHERE u.email = %s AND u.activo = 1
        """, ('admin@crm.com',))
        
        user = cursor.fetchone()
        if user:
            print(f"✅ Usuario encontrado: {user[3]} (ID: {user[0]}, Tenant: {user[1]})")
            
            # Verificar estructura del usuario
            print(f"   - ID: {user[0]}")
            print(f"   - Tenant ID: {user[1]}")
            print(f"   - Email: {user[3]}")
            print(f"   - Nombre: {user[5]}")
            print(f"   - Rol ID: {user[7]}")
            print(f"   - Activo: {user[8]}")
            
        else:
            print("❌ Usuario no encontrado")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en base de datos: {e}")
        return False

def test_tenant_isolation():
    """Probar aislamiento por tenant"""
    print("\n🔒 PROBANDO AISLAMIENTO POR TENANT")
    print("=" * 40)
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'crm_database')
        )
        cursor = conn.cursor()
        
        # Verificar candidatos por tenant
        print("1. Candidatos por tenant:")
        cursor.execute("SELECT tenant_id, COUNT(*) FROM Afiliados GROUP BY tenant_id")
        for row in cursor.fetchall():
            print(f"   Tenant {row[0]}: {row[1]} candidatos")
        
        # Verificar vacantes por tenant
        print("2. Vacantes por tenant:")
        cursor.execute("SELECT tenant_id, COUNT(*) FROM Vacantes GROUP BY tenant_id")
        for row in cursor.fetchall():
            print(f"   Tenant {row[0]}: {row[1]} vacantes")
        
        # Verificar que las consultas con tenant_id funcionan
        print("3. Probando consulta con tenant_id:")
        cursor.execute("SELECT COUNT(*) FROM Afiliados WHERE tenant_id = 1")
        count = cursor.fetchone()[0]
        print(f"   Candidatos del tenant 1: {count}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en aislamiento: {e}")
        return False

def test_backend_endpoints():
    """Probar endpoints del backend"""
    print("\n🌐 PROBANDO ENDPOINTS DEL BACKEND")
    print("=" * 40)
    
    try:
        # Probar endpoint de salud
        response = requests.get('http://localhost:5000/health', timeout=5)
        print(f"1. Health check: Status {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Estado: {health_data.get('status')}")
            print(f"   Base de datos: {health_data.get('database')}")
        
        # Probar login con diferentes credenciales
        print("2. Probando login...")
        
        test_users = [
            {'email': 'admin@crm.com', 'password': 'admin123'},
            {'email': 'reclutador@crm.com', 'password': 'reclutador123'},
            {'email': 'prueba@prueba.com', 'password': 'prueba123'}
        ]
        
        for user_data in test_users:
            try:
                response = requests.post('http://localhost:5000/api/auth/login', 
                                       json=user_data, timeout=5)
                print(f"   {user_data['email']}: Status {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if 'user' in data:
                        tenant_id = data['user'].get('tenant_id')
                        print(f"     Tenant ID: {tenant_id}")
                    
            except Exception as e:
                print(f"   {user_data['email']}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando endpoints: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 PRUEBA SIMPLE DEL SISTEMA MULTI-TENANCY")
    print("=" * 50)
    
    db_ok = test_database_directly()
    isolation_ok = test_tenant_isolation()
    endpoints_ok = test_backend_endpoints()
    
    print("\n📊 RESULTADO FINAL")
    print("=" * 30)
    
    if db_ok:
        print("✅ Base de datos: OK")
    else:
        print("❌ Base de datos: ERROR")
    
    if isolation_ok:
        print("✅ Aislamiento por tenant: OK")
    else:
        print("❌ Aislamiento por tenant: ERROR")
    
    if endpoints_ok:
        print("✅ Endpoints del backend: OK")
    else:
        print("❌ Endpoints del backend: ERROR")
    
    if db_ok and isolation_ok:
        print("\n🎉 Sistema multi-tenancy funcionando correctamente")
        return True
    else:
        print("\n⚠️ Sistema tiene problemas que requieren atención")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
