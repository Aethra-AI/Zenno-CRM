#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar que el token de autenticación funciona correctamente
"""

import requests
import json

class AuthTokenTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.token = None
        
    def test_login(self):
        """Probar login y obtener token"""
        print("🔐 Probando login...")
        
        login_data = {
            "email": "admin@crm.com",
            "password": "admin123"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                print(f"✅ Login exitoso")
                print(f"🔑 Token obtenido: {self.token[:50]}...")
                return True
            else:
                print(f"❌ Error en login: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def test_whatsapp_endpoints_with_token(self):
        """Probar endpoints de WhatsApp con token"""
        print("\n🔍 Probando endpoints de WhatsApp con token...")
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Probar endpoint de modo
        try:
            response = requests.get(f"{self.base_url}/api/whatsapp/mode", headers=headers)
            print(f"📊 Endpoint modo - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Modo obtenido: {data.get('mode')} - {data.get('description')}")
            else:
                print(f"❌ Error en modo: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en modo: {e}")
            return False
        
        # Probar endpoint de configuración
        try:
            response = requests.get(f"{self.base_url}/api/whatsapp/config", headers=headers)
            print(f"📊 Endpoint config - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Configuración obtenida - Modo: {data.get('config', {}).get('mode', 'N/A')}")
            else:
                print(f"❌ Error en config: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en config: {e}")
            return False
        
        return True
    
    def test_without_token(self):
        """Probar endpoints sin token (debe fallar)"""
        print("\n🚫 Probando endpoints sin token (debe fallar)...")
        
        try:
            response = requests.get(f"{self.base_url}/api/whatsapp/mode")
            print(f"📊 Sin token - Status: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ Correctamente rechazado sin token")
                return True
            else:
                print(f"❌ Debería haber fallado pero no falló: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 INICIANDO PRUEBAS DE TOKEN DE AUTENTICACIÓN")
        print("=" * 60)
        
        tests = [
            ("Login y obtener token", self.test_login),
            ("Endpoints con token", self.test_whatsapp_endpoints_with_token),
            ("Endpoints sin token", self.test_without_token)
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
            print("🎉 ¡Todas las pruebas pasaron! Autenticación funcionando.")
        else:
            print("⚠️ Algunas pruebas fallaron.")
        
        print(f"\n🔑 Token de prueba: {self.token[:50] if self.token else 'No obtenido'}...")
        
        print("\n📋 INSTRUCCIONES PARA FRONTEND:")
        print("1. Hacer login en el frontend con admin@crm.com / admin123")
        print("2. Verificar que se guarda 'auth_token' en localStorage")
        print("3. Ir a Configuración → WhatsApp")
        print("4. Debería cargar sin errores 401")

if __name__ == "__main__":
    tester = AuthTokenTester()
    tester.run_all_tests()
