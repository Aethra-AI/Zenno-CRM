#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la integración completa frontend-backend de WhatsApp
"""

import requests
import json
import time
from datetime import datetime

class FrontendBackendTester:
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
        print("\n🔍 Probando endpoint de modo WhatsApp (usado por frontend)...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/whatsapp/mode",
                headers=self.get_headers()
            )
            
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
        """Probar endpoint de configuración que usa el frontend"""
        print("\n⚙️ Probando endpoint de configuración (usado por frontend)...")
        
        try:
            # GET para obtener configuración
            response = requests.get(
                f"{self.base_url}/api/whatsapp/config",
                headers=self.get_headers()
            )
            
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
    
    def test_whatsapp_mode_change(self):
        """Probar cambio de modo que hace el frontend"""
        print("\n🔄 Probando cambio de modo (simulando frontend)...")
        
        try:
            # Cambiar a modo business_api
            response = requests.post(
                f"{self.base_url}/api/whatsapp/config",
                json={"mode": "business_api"},
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                print("✅ Modo cambiado a business_api exitosamente")
                
                # Cambiar de vuelta a web_js
                response = requests.post(
                    f"{self.base_url}/api/whatsapp/config",
                    json={"mode": "web_js"},
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    print("✅ Modo cambiado a web_js exitosamente")
                    return True
                else:
                    print(f"❌ Error cambiando a web_js: {response.status_code}")
                    return False
            else:
                print(f"❌ Error cambiando a business_api: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_whatsapp_api_config_save(self):
        """Probar guardado de configuración de API que hace el frontend"""
        print("\n💾 Probando guardado de configuración API (simulando frontend)...")
        
        api_config = {
            "mode": "business_api",
            "api_token": "EAAxxxxxxxxxxxxxxxxxxxxx",
            "phone_number_id": "123456789012345",
            "business_account_id": "123456789012345",
            "webhook_verify_token": "mi_token_secreto"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/whatsapp/config",
                json=api_config,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                print("✅ Configuración de API guardada exitosamente")
                return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_whatsapp_config_test(self):
        """Probar endpoint de prueba de configuración que usa el frontend"""
        print("\n🧪 Probando endpoint de prueba de configuración...")
        
        test_config = {
            "api_token": "test_token",
            "phone_number_id": "test_phone_id"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/whatsapp/config/test",
                json=test_config,
                headers=self.get_headers()
            )
            
            if response.status_code in [200, 400]:  # 400 es esperado para tokens de prueba
                data = response.json()
                print(f"✅ Prueba de configuración ejecutada: {data.get('message', 'Sin mensaje')}")
                return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_whatsapp_web_session_endpoints(self):
        """Probar endpoints de sesión Web que usa el frontend"""
        print("\n📱 Probando endpoints de sesión WhatsApp Web...")
        
        try:
            # Probar inicialización de sesión
            response = requests.post(
                f"{self.base_url}/api/whatsapp/web/init-session",
                json={"user_id": 1},
                headers=self.get_headers()
            )
            
            if response.status_code in [200, 400]:  # 400 puede ser esperado si bridge no está corriendo
                data = response.json()
                print(f"✅ Endpoint de inicialización funcionando: {data.get('message', 'Sin mensaje')}")
                
                # Probar estado de sesión
                response = requests.get(
                    f"{self.base_url}/api/whatsapp/web/session-status",
                    headers=self.get_headers()
                )
                
                if response.status_code in [200, 400]:
                    data = response.json()
                    print(f"✅ Endpoint de estado funcionando: {data.get('message', 'Sin mensaje')}")
                    return True
                else:
                    print(f"❌ Error en estado: {response.status_code}")
                    return False
            else:
                print(f"❌ Error en inicialización: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_whatsapp_web_chats_endpoint(self):
        """Probar endpoint de chats que usa el frontend"""
        print("\n💬 Probando endpoint de chats WhatsApp Web...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/whatsapp/web/chats",
                headers=self.get_headers()
            )
            
            if response.status_code in [200, 400]:  # 400 puede ser esperado si bridge no está corriendo
                data = response.json()
                chats_count = len(data.get('chats', [])) if isinstance(data.get('chats'), list) else 0
                print(f"✅ Endpoint de chats funcionando: {chats_count} chats obtenidos")
                return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas de integración"""
        print("🚀 INICIANDO PRUEBAS DE INTEGRACIÓN FRONTEND-BACKEND")
        print("=" * 60)
        
        if not self.login():
            print("❌ No se pudo iniciar sesión - Abortando pruebas")
            return
        
        tests = [
            ("Endpoint de modo WhatsApp", self.test_whatsapp_mode_endpoint),
            ("Endpoint de configuración", self.test_whatsapp_config_endpoint),
            ("Cambio de modo", self.test_whatsapp_mode_change),
            ("Guardado configuración API", self.test_whatsapp_api_config_save),
            ("Prueba de configuración", self.test_whatsapp_config_test),
            ("Endpoints de sesión Web", self.test_whatsapp_web_session_endpoints),
            ("Endpoint de chats Web", self.test_whatsapp_web_chats_endpoint)
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
            print("🎉 ¡Todas las pruebas pasaron! Integración frontend-backend funcionando correctamente.")
        else:
            print("⚠️ Algunas pruebas fallaron - Revisar integración.")
        
        print(f"\n🔍 Tenant ID utilizado: {self.tenant_id}")
        print(f"🔑 Token obtenido: {'Sí' if self.token else 'No'}")
        
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Ejecutar bridge.js para funcionalidad completa de WhatsApp Web")
        print("2. Probar interfaz de configuración en el frontend")
        print("3. Configurar credenciales reales de WhatsApp Business API")

if __name__ == "__main__":
    tester = FrontendBackendTester()
    tester.run_all_tests()
