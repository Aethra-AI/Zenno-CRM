#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple para probar los endpoints del calendario
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"

def login():
    """Iniciar sesión y obtener token"""
    login_data = {
        "email": "admin@crm.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        if response.status_code == 200:
            data = response.json()
            return data.get('token')
        else:
            print(f"❌ Error en login: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
        return None

def test_simple_endpoint(token):
    """Probar un endpoint simple primero"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n🧪 Probando endpoint simple...")
    try:
        response = requests.get(f"{BASE_URL}/api/calendar/reminders", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("🚀 Iniciando prueba simple...")
    
    # Iniciar sesión
    token = login()
    if not token:
        print("❌ No se pudo obtener el token")
        return
    
    print("✅ Token obtenido")
    
    # Probar endpoint
    test_simple_endpoint(token)

if __name__ == "__main__":
    main()
