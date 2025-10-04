#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_vacancies_fields():
    base_url = "http://localhost:5000"
    
    # Test login first
    login_data = {
        "email": "admin@crm.com",
        "password": "admin123"
    }
    
    print("🔐 Testing login...")
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json().get('token')
            headers = {"Authorization": f"Bearer {token}"}
            
            print(f"✅ Login successful, token: {token[:20]}...")
            
            # Test vacancies endpoint
            print("\n💼 Testing /api/vacancies...")
            vac_response = requests.get(f"{base_url}/api/vacancies", headers=headers)
            print(f"Vacancies Status: {vac_response.status_code}")
            if vac_response.status_code == 200:
                vacs = vac_response.json()
                print(f"Vacancies Count: {len(vacs.get('data', [])) if isinstance(vacs, dict) else len(vacs) if isinstance(vacs, list) else 'Unknown'}")
                
                # Show first vacancy fields
                if isinstance(vacs, dict) and vacs.get('data'):
                    first_vacancy = vacs['data'][0]
                    print(f"\nFirst vacancy fields:")
                    for key, value in first_vacancy.items():
                        print(f"  {key}: {value}")
                elif isinstance(vacs, list) and len(vacs) > 0:
                    first_vacancy = vacs[0]
                    print(f"\nFirst vacancy fields:")
                    for key, value in first_vacancy.items():
                        print(f"  {key}: {value}")
            else:
                print(f"Vacancies Error: {vac_response.text}")
                
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_vacancies_fields()

