#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar que el frontend puede cargar correctamente
"""

import requests
import json
import time

class FrontendLoadingTester:
    def __init__(self):
        self.backend_url = "http://localhost:5000"
        self.frontend_url = "http://localhost:5173"
        self.token = None
        
    def test_backend_running(self):
        """Verificar que el backend esté ejecutándose"""
        print("🔍 Verificando que el backend esté ejecutándose...")
        
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend ejecutándose correctamente")
                return True
        except requests.exceptions.RequestException:
            pass
        
        try:
            # Probar con endpoint de login
            response = requests.post(f"{self.backend_url}/api/auth/login", 
                                   json={"email": "admin@crm.com", "password": "admin123"}, 
                                   timeout=5)
            if response.status_code == 200:
                print("✅ Backend ejecutándose correctamente (login funciona)")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print("❌ Backend no está ejecutándose o no responde")
        return False
    
    def test_frontend_running(self):
        """Verificar que el frontend esté ejecutándose"""
        print("🔍 Verificando que el frontend esté ejecutándose...")
        
        try:
            response = requests.get(f"{self.frontend_url}", timeout=5)
            if response.status_code == 200 and "html" in response.text.lower():
                print("✅ Frontend ejecutándose correctamente")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print("❌ Frontend no está ejecutándose o no responde")
        return False
    
    def test_whatsapp_endpoints(self):
        """Probar endpoints de WhatsApp específicos"""
        print("🔍 Probando endpoints de WhatsApp...")
        
        # Login primero
        try:
            login_response = requests.post(f"{self.backend_url}/api/auth/login", 
                                         json={"email": "admin@crm.com", "password": "admin123"})
            
            if login_response.status_code != 200:
                print("❌ Error en login")
                return False
            
            token = login_response.json()['token']
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            
            # Probar endpoint de modo
            mode_response = requests.get(f"{self.backend_url}/api/whatsapp/mode", headers=headers)
            if mode_response.status_code == 200:
                print("✅ Endpoint de modo WhatsApp funcionando")
            else:
                print(f"❌ Error en endpoint de modo: {mode_response.status_code}")
                return False
            
            # Probar endpoint de configuración
            config_response = requests.get(f"{self.backend_url}/api/whatsapp/config", headers=headers)
            if config_response.status_code == 200:
                print("✅ Endpoint de configuración WhatsApp funcionando")
            else:
                print(f"❌ Error en endpoint de configuración: {config_response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error probando endpoints: {e}")
            return False
    
    def test_cors_headers(self):
        """Probar headers CORS"""
        print("🔍 Probando headers CORS...")
        
        try:
            # Simular petición desde frontend
            headers = {
                'Origin': 'http://localhost:5173',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Authorization, Content-Type'
            }
            
            response = requests.options(f"{self.backend_url}/api/whatsapp/mode", headers=headers)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if cors_headers['Access-Control-Allow-Origin']:
                print("✅ Headers CORS configurados correctamente")
                print(f"   Allow-Origin: {cors_headers['Access-Control-Allow-Origin']}")
                return True
            else:
                print("❌ Headers CORS no configurados")
                return False
                
        except Exception as e:
            print(f"❌ Error probando CORS: {e}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 INICIANDO PRUEBAS DE CARGA DEL FRONTEND")
        print("=" * 60)
        
        tests = [
            ("Backend ejecutándose", self.test_backend_running),
            ("Frontend ejecutándose", self.test_frontend_running),
            ("Endpoints WhatsApp", self.test_whatsapp_endpoints),
            ("Headers CORS", self.test_cors_headers)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                print()  # Línea en blanco entre pruebas
            except Exception as e:
                print(f"❌ Error en {test_name}: {e}")
                print()
        
        print("=" * 60)
        print(f"📊 RESULTADOS: {passed}/{total} pruebas pasaron")
        
        if passed == total:
            print("🎉 ¡Todas las pruebas pasaron! Sistema listo.")
        else:
            print("⚠️ Algunas pruebas fallaron.")
        
        print("\n📋 INSTRUCCIONES:")
        print("1. Si el backend no está ejecutándose:")
        print("   cd bACKEND && python app.py")
        print()
        print("2. Si el frontend no está ejecutándose:")
        print("   cd zenno-canvas-flow-main && npm run dev")
        print()
        print("3. Si hay errores en el frontend:")
        print("   - Abrir F12 en el navegador")
        print("   - Ir a la pestaña Console")
        print("   - Recargar la página")
        print("   - Revisar errores en consola")

if __name__ == "__main__":
    tester = FrontendLoadingTester()
    tester.run_all_tests()
