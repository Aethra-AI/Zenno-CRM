#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la conexión del frontend con el backend
"""

import requests
import json
from datetime import datetime

class FrontendConnectionTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.token = None
        self.tenant_id = None
        
    def login(self):
        """Iniciar sesión y obtener token"""
        print("🔐 Iniciando sesión...")
        
        login_data = {
            "email": "admin@crm.com",
            "password": "admin123"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                self.tenant_id = data['user']['tenant_id']
                print(f"✅ Login exitoso - Tenant ID: {self.tenant_id}")
                return True
            else:
                print(f"❌ Error en login: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def get_headers(self):
        """Obtener headers con token de autenticación"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def test_whatsapp_mode_endpoint(self):
        """Probar endpoint que usa el frontend para obtener el modo"""
        print("\n🔍 Probando endpoint de modo WhatsApp...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/whatsapp/mode",
                headers=self.get_headers()
            )
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📋 Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Modo obtenido: {data.get('mode')} - {data.get('description')}")
                return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_whatsapp_config_endpoint(self):
        """Probar endpoint de configuración"""
        print("\n⚙️ Probando endpoint de configuración...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/whatsapp/config",
                headers=self.get_headers()
            )
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📋 Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Configuración obtenida - Modo: {data.get('config', {}).get('mode', 'N/A')}")
                return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_cors_headers(self):
        """Probar headers CORS"""
        print("\n🌐 Probando headers CORS...")
        
        try:
            # Hacer una petición OPTIONS para verificar CORS
            response = requests.options(
                f"{self.base_url}/api/whatsapp/mode",
                headers={
                    'Origin': 'http://localhost:5173',
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Authorization, Content-Type'
                }
            )
            
            print(f"📊 OPTIONS Status Code: {response.status_code}")
            print(f"📋 CORS Headers: {dict(response.headers)}")
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            print(f"✅ CORS Headers: {cors_headers}")
            return True
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 INICIANDO PRUEBAS DE CONEXIÓN FRONTEND-BACKEND")
        print("=" * 60)
        
        if not self.login():
            print("❌ No se pudo iniciar sesión - Abortando pruebas")
            return
        
        tests = [
            ("Endpoint de modo WhatsApp", self.test_whatsapp_mode_endpoint),
            ("Endpoint de configuración", self.test_whatsapp_config_endpoint),
            ("Headers CORS", self.test_cors_headers)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ Error en {test_name}: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 RESULTADOS: {passed}/{total} pruebas pasaron")
        
        if passed == total:
            print("🎉 ¡Todas las pruebas pasaron! Backend listo para frontend.")
        else:
            print("⚠️ Algunas pruebas fallaron - Revisar configuración.")
        
        print(f"\n🔍 Tenant ID utilizado: {self.tenant_id}")
        print(f"🔑 Token obtenido: {'Sí' if self.token else 'No'}")
        
        print("\n📋 INSTRUCCIONES PARA FRONTEND:")
        print("1. Asegúrate de que el frontend esté ejecutándose en http://localhost:5173")
        print("2. Ve a Configuración → WhatsApp en el frontend")
        print("3. Deberías ver la configuración sin errores")
        print("4. Si hay errores, revisar la consola del navegador")

if __name__ == "__main__":
    tester = FrontendConnectionTester()
    tester.run_all_tests()
