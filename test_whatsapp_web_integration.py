"""
Test de Integración de WhatsApp Web.js Multi-Tenant
==================================================
Prueba la integración completa de WhatsApp Web.js con el sistema multi-tenant.
"""

import requests
import json
import time

# Configuración
BASE_URL = "http://localhost:5000"
TEST_TOKEN = None  # Se obtendrá del login
TEST_TENANT_ID = 1

class WhatsAppWebIntegrationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.tenant_id = TEST_TENANT_ID
        
    def login(self):
        """Obtener token de autenticación"""
        print("🔐 Iniciando sesión...")
        
        login_data = {
            "email": "admin@crm.com",
            "password": "admin123"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            print(f"✅ Login exitoso - Token obtenido")
            return True
        else:
            print(f"❌ Error en login: {response.status_code} - {response.text}")
            return False
    
    def get_headers(self):
        """Obtener headers con autenticación"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def test_whatsapp_mode(self):
        """Probar obtención del modo de WhatsApp"""
        print("\n🔍 Probando obtención del modo de WhatsApp...")
        
        response = requests.get(
            f"{self.base_url}/api/whatsapp/mode",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                mode = result.get('mode')
                description = result.get('description')
                print(f"✅ Modo obtenido: {mode} - {description}")
                return mode
            else:
                print(f"❌ Error obteniendo modo: {result.get('message')}")
                return None
        else:
            print(f"❌ Error en request: {response.status_code} - {response.text}")
            return None
    
    def test_web_session_init(self):
        """Probar inicialización de sesión Web"""
        print("\n🚀 Probando inicialización de sesión WhatsApp Web...")
        
        session_data = {
            "user_id": 1
        }
        
        response = requests.post(
            f"{self.base_url}/api/whatsapp/web/init-session",
            json=session_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                session_id = result.get('session_id')
                print(f"✅ Sesión Web inicializada: {session_id}")
                return session_id
            else:
                print(f"❌ Error inicializando sesión: {result.get('error')}")
                return None
        else:
            print(f"❌ Error en request: {response.status_code} - {response.text}")
            return None
    
    def test_web_session_status(self):
        """Probar estado de sesión Web"""
        print("\n📊 Probando estado de sesión WhatsApp Web...")
        
        response = requests.get(
            f"{self.base_url}/api/whatsapp/web/session-status",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                session_status = result.get('session_status')
                is_ready = result.get('is_ready')
                qr_code = result.get('qr_code')
                
                print(f"✅ Estado obtenido: {session_status}")
                print(f"   Listo: {is_ready}")
                if qr_code:
                    print(f"   QR Code disponible: {len(qr_code)} caracteres")
                return result
            else:
                print(f"❌ Error obteniendo estado: {result.get('error')}")
                return None
        else:
            print(f"❌ Error en request: {response.status_code} - {response.text}")
            return None
    
    def test_web_chats(self):
        """Probar obtención de chats Web"""
        print("\n💬 Probando obtención de chats WhatsApp Web...")
        
        response = requests.get(
            f"{self.base_url}/api/whatsapp/web/chats",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                chats = result.get('chats', [])
                print(f"✅ {len(chats)} chats obtenidos")
                return chats
            else:
                print(f"❌ Error obteniendo chats: {result.get('error')}")
                return None
        else:
            print(f"❌ Error en request: {response.status_code} - {response.text}")
            return None
    
    def test_hybrid_message_send(self):
        """Probar envío de mensaje híbrido"""
        print("\n📤 Probando envío de mensaje híbrido...")
        
        message_data = {
            "to": "573001234567",
            "message": "Hola! Este es un mensaje de prueba desde el sistema híbrido.",
            "type": "text"
        }
        
        response = requests.post(
            f"{self.base_url}/api/whatsapp/send-message",
            json=message_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                message_id = result.get('message_id')
                mode = result.get('mode', 'unknown')
                print(f"✅ Mensaje enviado - ID: {message_id}, Modo: {mode}")
                return message_id
            else:
                print(f"❌ Error enviando mensaje: {result.get('message')}")
                return None
        else:
            print(f"❌ Error en request: {response.status_code} - {response.text}")
            return None
    
    def test_web_session_close(self):
        """Probar cierre de sesión Web"""
        print("\n🔒 Probando cierre de sesión WhatsApp Web...")
        
        response = requests.delete(
            f"{self.base_url}/api/whatsapp/web/close-session",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print(f"✅ Sesión cerrada exitosamente")
                return True
            else:
                print(f"❌ Error cerrando sesión: {result.get('error')}")
                return False
        else:
            print(f"❌ Error en request: {response.status_code} - {response.text}")
            return False
    
    def test_conversations_endpoint(self):
        """Probar endpoint de conversaciones"""
        print("\n💬 Probando endpoint de conversaciones...")
        
        response = requests.get(
            f"{self.base_url}/api/whatsapp/conversations",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                conversations = result.get('conversations', [])
                print(f"✅ {len(conversations)} conversaciones encontradas")
                return True
            else:
                print(f"❌ Error obteniendo conversaciones: {result.get('message')}")
                return False
        else:
            print(f"❌ Error en request: {response.status_code} - {response.text}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 INICIANDO PRUEBAS DE WHATSAPP WEB.JS INTEGRACIÓN")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Login
        total_tests += 1
        if self.login():
            tests_passed += 1
        
        # Test 2: Obtener modo WhatsApp
        total_tests += 1
        mode = self.test_whatsapp_mode()
        if mode:
            tests_passed += 1
        
        # Test 3: Inicializar sesión Web
        total_tests += 1
        session_id = self.test_web_session_init()
        if session_id:
            tests_passed += 1
        
        # Test 4: Estado de sesión Web
        total_tests += 1
        if self.test_web_session_status():
            tests_passed += 1
        
        # Test 5: Obtener chats Web
        total_tests += 1
        if self.test_web_chats():
            tests_passed += 1
        
        # Test 6: Envío de mensaje híbrido
        total_tests += 1
        message_id = self.test_hybrid_message_send()
        if message_id:
            tests_passed += 1
        
        # Test 7: Conversaciones
        total_tests += 1
        if self.test_conversations_endpoint():
            tests_passed += 1
        
        # Test 8: Cerrar sesión Web
        total_tests += 1
        if self.test_web_session_close():
            tests_passed += 1
        
        # Resultados
        print("\n" + "=" * 60)
        print(f"📊 RESULTADOS: {tests_passed}/{total_tests} pruebas pasaron")
        
        if tests_passed == total_tests:
            print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
            print("✅ Sistema de WhatsApp Web.js híbrido funcionando correctamente")
        else:
            print("⚠️ Algunas pruebas fallaron - Revisar configuración")
        
        return tests_passed == total_tests

if __name__ == "__main__":
    tester = WhatsAppWebIntegrationTester()
    tester.run_all_tests()

