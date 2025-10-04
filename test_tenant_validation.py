#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba completo para validar que todas las operaciones
de WhatsApp incluyan tenant ID correctamente
"""

import requests
import json
import time
from datetime import datetime

class TenantValidationTester:
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
    
    def test_whatsapp_mode(self):
        """Probar obtención del modo de WhatsApp"""
        print("\n🔍 Probando obtención del modo de WhatsApp...")
        
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
    
    def test_whatsapp_config(self):
        """Probar configuración de WhatsApp"""
        print("\n⚙️ Probando configuración de WhatsApp...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/whatsapp/config",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Configuración obtenida - Tenant ID en respuesta: {data.get('tenant_id')}")
                return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_web_session_init(self):
        """Probar inicialización de sesión WhatsApp Web"""
        print("\n🚀 Probando inicialización de sesión WhatsApp Web...")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/whatsapp/web/init-session",
                json={"user_id": 1},
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Sesión Web inicializada: {data.get('session_id')}")
                return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_web_session_status(self):
        """Probar estado de sesión WhatsApp Web"""
        print("\n📊 Probando estado de sesión WhatsApp Web...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/whatsapp/web/session-status",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Estado obtenido: {data.get('status')} - {data.get('message')}")
                return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_web_chats(self):
        """Probar obtención de chats WhatsApp Web"""
        print("\n💬 Probando obtención de chats WhatsApp Web...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/whatsapp/web/chats",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                chats_count = len(data.get('chats', []))
                print(f"✅ {chats_count} chats obtenidos")
                return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_message_send(self):
        """Probar envío de mensaje"""
        print("\n📤 Probando envío de mensaje...")
        
        message_data = {
            "to": "1234567890",
            "message": "Mensaje de prueba desde script de validación",
            "type": "text"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/whatsapp/send-message",
                json=message_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Mensaje enviado: {data.get('message')}")
                return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_conversations(self):
        """Probar endpoint de conversaciones"""
        print("\n💬 Probando endpoint de conversaciones...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/whatsapp/conversations",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                conv_count = len(data.get('conversations', []))
                print(f"✅ {conv_count} conversaciones encontradas")
                return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_webhook_validation(self):
        """Probar validación de webhook"""
        print("\n🔗 Probando validación de webhook...")
        
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "test_entry",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test_phone_id"
                        },
                        "messages": [{
                            "from": "1234567890",
                            "id": "test_message_id",
                            "timestamp": str(int(time.time())),
                            "text": {"body": "Mensaje de prueba webhook"},
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/whatsapp/webhook",
                json=webhook_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Webhook procesado: {data.get('status')}")
                return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def validate_tenant_in_database(self):
        """Validar que los datos se guarden con tenant ID en la base de datos"""
        print("\n🗄️ Validando tenant ID en base de datos...")
        
        try:
            # Verificar conversaciones con tenant ID
            response = requests.get(
                f"{self.base_url}/api/whatsapp/conversations",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                conversations = data.get('conversations', [])
                
                for conv in conversations:
                    if conv.get('tenant_id') == self.tenant_id:
                        print(f"✅ Conversación {conv.get('id')} tiene tenant_id correcto: {conv.get('tenant_id')}")
                    else:
                        print(f"❌ Conversación {conv.get('id')} tiene tenant_id incorrecto: {conv.get('tenant_id')}")
                        return False
                
                print(f"✅ Todas las {len(conversations)} conversaciones tienen tenant_id correcto")
                return True
            else:
                print(f"❌ Error obteniendo conversaciones: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 INICIANDO VALIDACIÓN COMPLETA DE TENANT ID")
        print("=" * 60)
        
        if not self.login():
            print("❌ No se pudo iniciar sesión - Abortando pruebas")
            return
        
        tests = [
            ("Modo WhatsApp", self.test_whatsapp_mode),
            ("Configuración WhatsApp", self.test_whatsapp_config),
            ("Inicialización sesión Web", self.test_web_session_init),
            ("Estado sesión Web", self.test_web_session_status),
            ("Chats WhatsApp Web", self.test_web_chats),
            ("Envío de mensaje", self.test_message_send),
            ("Conversaciones", self.test_conversations),
            ("Webhook", self.test_webhook_validation),
            ("Validación BD", self.validate_tenant_in_database)
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
            print("🎉 ¡Todas las pruebas pasaron! Sistema validado correctamente.")
        else:
            print("⚠️ Algunas pruebas fallaron - Revisar implementación.")
        
        print(f"\n🔍 Tenant ID utilizado: {self.tenant_id}")
        print(f"🔑 Token obtenido: {'Sí' if self.token else 'No'}")

if __name__ == "__main__":
    tester = TenantValidationTester()
    tester.run_all_tests()
