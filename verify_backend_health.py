#!/usr/bin/env python3
"""
Script para verificar que el backend esté funcionando correctamente
antes de ejecutar las pruebas del sistema multi-tenancy
"""

import requests
import json
import time

def check_backend_health():
    """Verificar que el backend esté funcionando"""
    BASE_URL = "http://localhost:5000"
    
    print("🔍 VERIFICANDO SALUD DEL BACKEND")
    print("=" * 40)
    
    # 1. Verificar que el servidor responde
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor respondiendo correctamente")
            health_data = response.json()
            print(f"   Estado: {health_data.get('status', 'unknown')}")
            print(f"   Base de datos: {health_data.get('database', 'unknown')}")
        else:
            print(f"⚠️ Servidor responde pero con status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor")
        print("   Verificar que el backend esté corriendo en http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error verificando servidor: {str(e)}")
        return False
    
    # 2. Verificar endpoint de login
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@crm.com",
            "password": "admin123"
        }, timeout=10)
        
        if response.status_code == 200:
            print("✅ Endpoint de login funcionando")
            data = response.json()
            if 'token' in data and 'user' in data:
                print(f"   Usuario: {data['user'].get('email', 'unknown')}")
                print(f"   Tenant ID: {data['user'].get('tenant_id', 'unknown')}")
                return True
            else:
                print("⚠️ Login responde pero formato incorrecto")
                return False
        else:
            print(f"❌ Login falló con status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando login: {str(e)}")
        return False

def check_database_connection():
    """Verificar conexión a la base de datos"""
    print("\n🗄️ VERIFICANDO CONEXIÓN A BASE DE DATOS")
    print("=" * 40)
    
    try:
        import mysql.connector
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'crm_database')
        )
        
        cursor = conn.cursor()
        
        # Verificar tablas principales
        tables_to_check = ['Users', 'Tenants', 'Afiliados', 'Vacantes', 'Postulaciones']
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ Tabla {table}: {count} registros")
            except Exception as e:
                print(f"❌ Error en tabla {table}: {str(e)}")
                return False
        
        cursor.close()
        conn.close()
        
        print("✅ Base de datos funcionando correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a base de datos: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🚀 VERIFICACIÓN PREVIA DEL SISTEMA")
    print("=" * 50)
    
    backend_ok = check_backend_health()
    db_ok = check_database_connection()
    
    print("\n📊 RESULTADO FINAL")
    print("=" * 30)
    
    if backend_ok and db_ok:
        print("✅ Sistema listo para pruebas")
        print("   Puedes ejecutar: python test_tenant_system.py")
        return True
    else:
        print("❌ Sistema no está listo")
        if not backend_ok:
            print("   - Backend no está funcionando correctamente")
        if not db_ok:
            print("   - Base de datos no está accesible")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
