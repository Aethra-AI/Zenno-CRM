#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para debuggear el endpoint de login
"""

import requests
import json

def test_login():
    """Probar login y ver respuesta completa"""
    
    base_url = "http://localhost:5000"
    
    login_data = {
        "email": "admin@crm.com",
        "password": "admin123"
    }
    
    try:
        print("🔐 Probando login...")
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        try:
            data = response.json()
            print(f"📄 JSON Response: {json.dumps(data, indent=2)}")
        except:
            print(f"📄 Text Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login exitoso")
        else:
            print("❌ Login falló")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login()
