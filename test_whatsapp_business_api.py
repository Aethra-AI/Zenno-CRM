"""
Test de Integración Completa de WhatsApp Business API
===================================================
Prueba todos los componentes del sistema de WhatsApp multi-tenant.
"""

import requests
import json
import time
import mysql.connector
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000"
TEST_TOKEN = None  # Se obtendrá del login
TEST_TENANT_ID = 1

# Configuración de base de datos
DB_CONFIG = {
    'host': 'localhost',
    'database': 'reclutamiento_db',
    'user': 'root',
    'password': 'admin123'
}

class WhatsAppBusinessAPITester:
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
    
    def test_whatsapp_config(self):
        """Probar configuración de WhatsApp"""
        print("\n📋 Probando configuración de WhatsApp...")
        
        # Crear configuración de prueba
        config_data = {
            "api_type": "business_api",
            "business_api_token": "EAAxxxxxxxxxxxxxxxxxxxxx",  # Token de prueba
            "phone_number_id": "123456789012345",
            "webhook_url": "https://tu-dominio.com/api/whatsapp/webhook",
            "business_account_id": "987654321098765",
            "active": True
        }
        
        response = requests.post(
            f"{self.base_url}/api/whatsapp/config",
            json=config_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            print("✅ Configuración creada exitosamente")
            return True
        else:
            print(f"❌ Error creando configuración: {response.status_code} - {response.text}")
            return False
    
    def test_send_text_message(self):
        """Probar envío de mensaje de texto"""
        print("\n📤 Probando envío de mensaje de texto...")
        
        message_data = {
            "to": "573001234567",  # Número de prueba
            "message": "Hola! Este es un mensaje de prueba desde el CRM.",
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
                print(f"✅ Mensaje enviado - ID: {result.get('message_id')}")
                return result.get('message_id')
            else:
                print(f"❌ Error enviando mensaje: {result.get('message')}")
                return None
        else:
            print(f"❌ Error en request: {response.status_code} - {response.text}")
            return None
    
    def test_send_template_message(self):
        """Probar envío de mensaje template"""
        print("\n📋 Probando envío de mensaje template...")
        
        template_data = {
            "to": "573001234567",
            "message": "hello_world",  # Para templates, message contiene el nombre del template
            "type": "template",
            "template_params": ["Juan", "CRM"]
        }
        
        response = requests.post(
            f"{self.base_url}/api/whatsapp/send-message",
            json=template_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Template enviado - ID: {result.get('message_id')}")
                return result.get('message_id')
            else:
                print(f"❌ Error enviando template: {result.get('message')}")
                return None
        else:
            print(f"❌ Error en request: {response.status_code} - {response.text}")
            return None
    
    def test_send_media_message(self):
        """Probar envío de mensaje multimedia"""
        print("\n📷 Probando envío de mensaje multimedia...")
        
        media_data = {
            "to": "573001234567",
            "message": "image",  # Para media, message contiene el tipo
            "type": "image",
            "media_url": "https://via.placeholder.com/300x200/0000FF/FFFFFF?text=Test+Image",
            "caption": "Esta es una imagen de prueba desde el CRM"
        }
        
        response = requests.post(
            f"{self.base_url}/api/whatsapp/send-message",
            json=media_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Media enviado - ID: {result.get('message_id')}")
                return result.get('message_id')
            else:
                print(f"❌ Error enviando media: {result.get('message')}")
                return None
        else:
            print(f"❌ Error en request: {response.status_code} - {response.text}")
            return None
    
    def test_message_status(self, message_id):
        """Probar obtención de estado de mensaje"""
        if not message_id:
            print("\n⏭️ Saltando prueba de estado - No hay message_id")
            return False
            
        print(f"\n📊 Probando estado del mensaje {message_id}...")
        
        response = requests.get(
            f"{self.base_url}/api/whatsapp/message-status/{message_id}",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Estado obtenido: {result.get('message_status')}")
                return True
            else:
                print(f"❌ Error obteniendo estado: {result.get('message')}")
                return False
        else:
            print(f"❌ Error en request: {response.status_code} - {response.text}")
            return False
    
    def test_conversations(self):
        """Probar obtención de conversaciones"""
        print("\n💬 Probando obtención de conversaciones...")
        
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
    
    def test_whatsapp_stats(self):
        """Probar estadísticas de WhatsApp"""
        print("\n📈 Probando estadísticas de WhatsApp...")
        
        response = requests.get(
            f"{self.base_url}/api/whatsapp/stats",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                stats = result.get('stats', {})
                print(f"✅ Estadísticas obtenidas: {stats}")
                return True
            else:
                print(f"❌ Error obteniendo estadísticas: {result.get('message')}")
                return False
        else:
            print(f"❌ Error en request: {response.status_code} - {response.text}")
            return False
    
    def check_database_data(self):
        """Verificar datos en la base de datos"""
        print("\n🗄️ Verificando datos en base de datos...")
        
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            
            # Verificar conversaciones
            cursor.execute("SELECT COUNT(*) as count FROM WhatsApp_Conversations WHERE tenant_id = %s", (self.tenant_id,))
            conversations_count = cursor.fetchone()['count']
            print(f"📊 Conversaciones en BD: {conversations_count}")
            
            # Verificar mensajes
            cursor.execute("SELECT COUNT(*) as count FROM WhatsApp_Messages WHERE tenant_id = %s", (self.tenant_id,))
            messages_count = cursor.fetchone()['count']
            print(f"📨 Mensajes en BD: {messages_count}")
            
            # Verificar configuración
            cursor.execute("SELECT COUNT(*) as count FROM WhatsApp_Config WHERE tenant_id = %s", (self.tenant_id,))
            config_count = cursor.fetchone()['count']
            print(f"⚙️ Configuraciones en BD: {config_count}")
            
            cursor.close()
            conn.close()
            
            print("✅ Verificación de base de datos completada")
            return True
            
        except Exception as e:
            print(f"❌ Error verificando BD: {e}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 INICIANDO PRUEBAS DE WHATSAPP BUSINESS API")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Login
        total_tests += 1
        if self.login():
            tests_passed += 1
        
        # Test 2: Configuración
        total_tests += 1
        if self.test_whatsapp_config():
            tests_passed += 1
        
        # Test 3: Envío de mensaje texto
        total_tests += 1
        text_message_id = self.test_send_text_message()
        if text_message_id:
            tests_passed += 1
        
        # Test 4: Envío de template
        total_tests += 1
        template_message_id = self.test_send_template_message()
        if template_message_id:
            tests_passed += 1
        
        # Test 5: Envío de media
        total_tests += 1
        media_message_id = self.test_send_media_message()
        if media_message_id:
            tests_passed += 1
        
        # Test 6: Estado de mensaje
        total_tests += 1
        if self.test_message_status(text_message_id):
            tests_passed += 1
        
        # Test 7: Conversaciones
        total_tests += 1
        if self.test_conversations():
            tests_passed += 1
        
        # Test 8: Estadísticas
        total_tests += 1
        if self.test_whatsapp_stats():
            tests_passed += 1
        
        # Test 9: Base de datos
        total_tests += 1
        if self.check_database_data():
            tests_passed += 1
        
        # Resultados
        print("\n" + "=" * 60)
        print(f"📊 RESULTADOS: {tests_passed}/{total_tests} pruebas pasaron")
        
        if tests_passed == total_tests:
            print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
            print("✅ Sistema de WhatsApp Business API funcionando correctamente")
        else:
            print("⚠️ Algunas pruebas fallaron - Revisar configuración")
        
        return tests_passed == total_tests

if __name__ == "__main__":
    tester = WhatsAppBusinessAPITester()
    tester.run_all_tests()
