"""
Test Simple de Login
===================
Probar diferentes usuarios para encontrar uno válido.
"""

import requests
import json

def test_login():
    """Probar login con diferentes usuarios"""
    print("🔐 Probando login con diferentes usuarios...")
    
    users = [
        {'email': 'admin@test.com', 'password': 'admin123'},
        {'email': 'admin@admin.com', 'password': 'admin123'},
        {'email': 'test@test.com', 'password': 'test123'},
        {'email': 'admin', 'password': 'admin'},
        {'email': 'admin@reclutamiento.com', 'password': 'admin123'}
    ]
    
    for user in users:
        try:
            print(f"\n👤 Probando: {user['email']}")
            response = requests.post('http://localhost:5000/api/auth/login', json=user)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token', 'No token')
                print(f"   ✅ Login exitoso!")
                print(f"   Token: {token[:50]}...")
                return user, token
            else:
                print(f"   ❌ Error: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n❌ No se pudo hacer login con ningún usuario")
    return None, None

if __name__ == "__main__":
    user, token = test_login()
