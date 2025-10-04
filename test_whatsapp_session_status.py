#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar el comportamiento del estado de sesión de WhatsApp Web
"""

import requests
import json

class WhatsAppSessionTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.token = None
        
    def login(self):
        """Hacer login y obtener token"""
        print("🔐 Haciendo login...")
        
        login_data = {
            "email": "admin@crm.com",
            "password": "admin123"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                print("✅ Login exitoso")
                return True
            else:
                print(f"❌ Error en login: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def test_session_status_without_session(self):
        """Probar estado de sesión cuando no hay sesión activa"""
        print("\n🔍 Probando estado de sesión sin sesión activa...")
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(f"{self.base_url}/api/whatsapp/web/session-status", headers=headers)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 400:
                data = response.json()
                print(f"✅ Respuesta esperada (400): {data.get('message')}")
                
                if 'No hay sesión activa' in data.get('message', ''):
                    print("✅ Mensaje correcto: 'No hay sesión activa'")
                    return True
                else:
                    print(f"⚠️ Mensaje inesperado: {data.get('message')}")
                    return False
            else:
                print(f"❌ Status inesperado: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_session_status_without_token(self):
        """Probar estado de sesión sin token"""
        print("\n🚫 Probando estado de sesión sin token...")
        
        try:
            response = requests.get(f"{self.base_url}/api/whatsapp/web/session-status")
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ Correctamente rechazado sin token (401)")
                return True
            else:
                print(f"❌ Status inesperado: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_whatsapp_mode(self):
        """Probar endpoint de modo para verificar que funciona"""
        print("\n⚙️ Probando endpoint de modo...")
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(f"{self.base_url}/api/whatsapp/mode", headers=headers)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Modo obtenido: {data.get('mode')} - {data.get('description')}")
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 INICIANDO PRUEBAS DE ESTADO DE SESIÓN WHATSAPP")
        print("=" * 60)
        
        if not self.login():
            print("❌ No se pudo hacer login - Abortando pruebas")
            return
        
        tests = [
            ("Estado de sesión sin sesión activa", self.test_session_status_without_session),
            ("Estado de sesión sin token", self.test_session_status_without_token),
            ("Endpoint de modo", self.test_whatsapp_mode)
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
            print("🎉 ¡Todas las pruebas pasaron! Comportamiento correcto.")
        else:
            print("⚠️ Algunas pruebas fallaron.")
        
        print("\n📋 EXPLICACIÓN:")
        print("✅ El error 'No hay sesión activa' es NORMAL")
        print("✅ Significa que WhatsApp Web no está conectado")
        print("✅ Para conectar: Hacer clic en 'Iniciar Sesión'")
        print("✅ Después de conectar, el error desaparecerá")
        
        print("\n🔧 INSTRUCCIONES PARA USUARIO:")
        print("1. Los errores en consola son NORMALES si no hay sesión activa")
        print("2. Para conectar WhatsApp Web:")
        print("   - Hacer clic en 'Iniciar Sesión'")
        print("   - Escanear código QR con WhatsApp")
        print("   - Una vez conectado, los errores desaparecerán")
        print("3. Para WhatsApp API: No necesitas sesión activa")

if __name__ == "__main__":
    tester = WhatsAppSessionTester()
    tester.run_all_tests()
