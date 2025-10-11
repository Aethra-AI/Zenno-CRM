#!/usr/bin/env python3
"""
🧪 SCRIPT DE PRUEBA DE PERMISOS
Prueba los endpoints localmente para depurar problemas de filtrado
"""

import requests
import json
from datetime import datetime

# =====================================================
# CONFIGURACIÓN
# =====================================================

# URL del backend (cambiar según tu entorno)
BASE_URL = "http://localhost:5000"  # Para pruebas locales
# BASE_URL = "https://149.130.160.182.sslip.io"  # Para pruebas en VM

# Credenciales de prueba (cambiar según tus usuarios)
TEST_USERS = {
    "admin": {
        "email": "admin@empresa.com",  # CAMBIAR
        "password": "tu_password"       # CAMBIAR
    },
    "supervisor": {
        "email": "supervisor@empresa.com",  # CAMBIAR
        "password": "tu_password"           # CAMBIAR
    },
    "reclutador": {
        "email": "reclutador@empresa.com",  # CAMBIAR
        "password": "tu_password"            # CAMBIAR
    }
}

# =====================================================
# FUNCIONES DE AYUDA
# =====================================================

def print_header(title):
    """Imprime un encabezado bonito"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(success, message):
    """Imprime resultado con icono"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def login(email, password):
    """Hace login y retorna el token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"email": email, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('token')
        else:
            print(f"❌ Login falló: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error en login: {str(e)}")
        return None

def get_current_user_info(token):
    """Obtiene información del usuario actual"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"❌ Error obteniendo info de usuario: {str(e)}")
        return None

# =====================================================
# PRUEBAS DE ENDPOINTS
# =====================================================

def test_get_users(token, user_type):
    """Prueba el endpoint GET /api/users"""
    print(f"\n📋 Probando GET /api/users como {user_type}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('data', [])
            total = len(users)
            
            print_result(True, f"Retornó {total} usuarios")
            
            # Mostrar detalles
            print(f"\n📊 Usuarios retornados:")
            for user in users[:5]:  # Mostrar solo los primeros 5
                print(f"  - ID: {user.get('id')}, Nombre: {user.get('nombre')}, "
                      f"Email: {user.get('email')}, Rol: {user.get('rol_nombre')}")
            
            if total > 5:
                print(f"  ... y {total - 5} más")
            
            # Verificar role del usuario actual
            current_role = data.get('current_user_role')
            print(f"\n🎭 Rol detectado del usuario actual: '{current_role}'")
            
            # Análisis
            if user_type == "admin" and total > 1:
                print_result(True, "Admin ve múltiples usuarios ✅")
            elif user_type == "reclutador" and total == 1:
                print_result(True, "Reclutador ve solo 1 usuario (él mismo) ✅")
            elif user_type == "reclutador" and total > 1:
                print_result(False, f"PROBLEMA: Reclutador ve {total} usuarios (debería ver solo 1)")
            elif user_type == "supervisor":
                print_result(True, f"Supervisor ve {total} usuarios (él + su equipo)")
            
            return data
        else:
            print_result(False, f"Error: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print_result(False, f"Excepción: {str(e)}")
        return None

def test_get_candidates(token, user_type):
    """Prueba el endpoint GET /api/candidates"""
    print(f"\n📋 Probando GET /api/candidates como {user_type}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/candidates",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get('data', [])
            total = data.get('pagination', {}).get('total', len(candidates))
            
            print_result(True, f"Retornó {total} candidatos")
            
            # Mostrar detalles
            if len(candidates) > 0:
                print(f"\n📊 Candidatos retornados:")
                for candidate in candidates[:5]:
                    print(f"  - ID: {candidate.get('id_afiliado')}, "
                          f"Nombre: {candidate.get('nombre')}")
                
                if len(candidates) > 5:
                    print(f"  ... y {len(candidates) - 5} más")
            else:
                print("  (Sin candidatos)")
            
            # Análisis
            if user_type == "reclutador" and total > 50:
                print_result(False, f"PROBLEMA: Reclutador ve {total} candidatos (demasiados)")
            elif user_type == "admin":
                print_result(True, f"Admin ve {total} candidatos")
            
            return data
        else:
            print_result(False, f"Error: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print_result(False, f"Excepción: {str(e)}")
        return None

def test_get_vacancies(token, user_type):
    """Prueba el endpoint GET /api/vacancies"""
    print(f"\n📋 Probando GET /api/vacancies como {user_type}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/vacancies",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # El endpoint puede retornar array directo o objeto con 'data'
            if isinstance(data, list):
                vacancies = data
                total = len(vacancies)
            else:
                vacancies = data.get('data', [])
                total = data.get('pagination', {}).get('total', len(vacancies))
            
            print_result(True, f"Retornó {total} vacantes")
            
            # Mostrar detalles
            if len(vacancies) > 0:
                print(f"\n📊 Vacantes retornadas:")
                for vacancy in vacancies[:5]:
                    print(f"  - ID: {vacancy.get('id_vacante')}, "
                          f"Cargo: {vacancy.get('cargo_solicitado')}")
                
                if len(vacancies) > 5:
                    print(f"  ... y {len(vacancies) - 5} más")
            else:
                print("  (Sin vacantes)")
            
            return data
        else:
            print_result(False, f"Error: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print_result(False, f"Excepción: {str(e)}")
        return None

def test_get_clients(token, user_type):
    """Prueba el endpoint GET /api/clients"""
    print(f"\n📋 Probando GET /api/clients como {user_type}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/clients",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # El endpoint puede retornar array directo o objeto con 'data'
            if isinstance(data, list):
                clients = data
                total = len(clients)
            else:
                clients = data.get('data', [])
                total = len(clients)
            
            print_result(True, f"Retornó {total} clientes")
            
            # Mostrar detalles
            if len(clients) > 0:
                print(f"\n📊 Clientes retornados:")
                for client in clients[:5]:
                    print(f"  - ID: {client.get('id_cliente')}, "
                          f"Empresa: {client.get('empresa')}")
                
                if len(clients) > 5:
                    print(f"  ... y {len(clients) - 5} más")
            else:
                print("  (Sin clientes)")
            
            return data
        else:
            print_result(False, f"Error: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print_result(False, f"Excepción: {str(e)}")
        return None

# =====================================================
# PRUEBA DETALLADA DE PERMISSION_SERVICE
# =====================================================

def test_permission_functions_directly():
    """Prueba directamente las funciones de permission_service"""
    print_header("PRUEBA DIRECTA DE PERMISSION_SERVICE")
    
    try:
        import sys
        sys.path.insert(0, '/Users/juanmontufar/Downloads/Crm Zenno /bACKEND')
        
        from permission_service import (
            is_admin, is_supervisor, is_recruiter,
            get_user_role_name, get_accessible_user_ids
        )
        
        # Probar con diferentes usuarios
        test_cases = [
            {"user_id": 1, "tenant_id": 1, "expected_role": "Admin"},
            {"user_id": 2, "tenant_id": 1, "expected_role": "Reclutador"},
            # Agregar más casos según tus usuarios
        ]
        
        for case in test_cases:
            user_id = case['user_id']
            tenant_id = case['tenant_id']
            expected = case['expected_role']
            
            print(f"\n🧪 Probando user_id={user_id}, tenant_id={tenant_id}")
            
            # Obtener rol
            role_name = get_user_role_name(user_id, tenant_id)
            print(f"  Rol obtenido: '{role_name}'")
            
            # Probar is_admin
            is_admin_result = is_admin(user_id, tenant_id)
            print(f"  is_admin(): {is_admin_result}")
            
            # Probar is_supervisor
            is_supervisor_result = is_supervisor(user_id, tenant_id)
            print(f"  is_supervisor(): {is_supervisor_result}")
            
            # Probar is_recruiter
            is_recruiter_result = is_recruiter(user_id, tenant_id)
            print(f"  is_recruiter(): {is_recruiter_result}")
            
            # Obtener usuarios accesibles
            accessible = get_accessible_user_ids(user_id, tenant_id)
            print(f"  Usuarios accesibles: {accessible}")
            
            # Verificar
            if expected == "Admin" and is_admin_result:
                print_result(True, "Admin detectado correctamente")
            elif expected == "Reclutador" and is_recruiter_result:
                print_result(True, "Reclutador detectado correctamente")
            else:
                print_result(False, f"Esperaba {expected}, pero no coincide")
        
        return True
        
    except ImportError as e:
        print_result(False, f"No se pudo importar permission_service: {str(e)}")
        print("  (Ejecuta este script desde el directorio bACKEND)")
        return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

# =====================================================
# MAIN - EJECUTAR TODAS LAS PRUEBAS
# =====================================================

def main():
    """Ejecutar todas las pruebas"""
    print_header("🧪 PRUEBA DE PERMISOS - CRM ZENNO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend: {BASE_URL}")
    
    # Opción 1: Prueba directa de funciones (si estamos en bACKEND/)
    print("\n" + "=" * 60)
    print("OPCIÓN 1: Probar funciones directamente")
    print("=" * 60)
    
    import os
    if os.path.exists('permission_service.py'):
        test_permission_functions_directly()
    else:
        print("⚠️  No estás en el directorio bACKEND/")
        print("   Salta al directorio correcto o ejecuta: cd bACKEND/")
    
    # Opción 2: Prueba de endpoints con diferentes usuarios
    print("\n" + "=" * 60)
    print("OPCIÓN 2: Probar endpoints con diferentes usuarios")
    print("=" * 60)
    
    user_type = input("\n¿Con qué tipo de usuario quieres probar? (admin/supervisor/reclutador): ").strip().lower()
    
    if user_type not in TEST_USERS:
        print("❌ Tipo de usuario no válido")
        return
    
    # Login
    print_header(f"LOGIN COMO {user_type.upper()}")
    credentials = TEST_USERS[user_type]
    print(f"Email: {credentials['email']}")
    
    token = login(credentials['email'], credentials['password'])
    
    if not token:
        print("❌ No se pudo obtener token. Verifica credenciales en TEST_USERS")
        return
    
    print_result(True, "Token obtenido")
    print(f"Token: {token[:50]}...")
    
    # Obtener info del usuario actual
    print_header("INFO DEL USUARIO ACTUAL")
    user_info = get_current_user_info(token)
    
    if user_info:
        print(f"ID: {user_info.get('id')}")
        print(f"Nombre: {user_info.get('nombre')}")
        print(f"Email: {user_info.get('email')}")
        print(f"Rol: {user_info.get('rol_nombre')}")
        print(f"Tenant ID: {user_info.get('tenant_id')}")
    
    # Probar endpoints
    print_header("PROBANDO ENDPOINTS")
    
    test_get_users(token, user_type)
    test_get_candidates(token, user_type)
    test_get_vacancies(token, user_type)
    test_get_clients(token, user_type)
    
    # Resumen
    print_header("RESUMEN")
    print(f"\n✅ Pruebas completadas para usuario tipo: {user_type}")
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Revisa los resultados arriba")
    print("2. Si un Reclutador ve más de 1 usuario → PROBLEMA")
    print("3. Si un Reclutador ve muchos candidatos → PROBLEMA")
    print("4. Compara resultados entre Admin y Reclutador")
    print("\n")

if __name__ == "__main__":
    main()




