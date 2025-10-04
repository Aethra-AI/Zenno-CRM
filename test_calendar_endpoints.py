#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar los endpoints del calendario
"""

import requests
import json
from datetime import datetime, date

# Configuración
BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
CALENDAR_URL = f"{BASE_URL}/api/calendar"

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

def test_calendar_endpoints(token):
    """Probar endpoints del calendario"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    current_date = datetime.now()
    year = current_date.year
    month = current_date.month
    
    print(f"🧪 Probando endpoints del calendario para {year}-{month:02d}")
    
    # Probar obtener recordatorios
    print("\n1. Probando GET /api/calendar/reminders...")
    try:
        response = requests.get(
            f"{CALENDAR_URL}/reminders?year={year}&month={month}",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Recordatorios obtenidos: {len(data.get('data', []))} registros")
            for reminder in data.get('data', [])[:3]:  # Mostrar solo los primeros 3
                print(f"   - {reminder.get('title')} ({reminder.get('type')})")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Probar crear recordatorio
    print("\n2. Probando POST /api/calendar/reminders...")
    try:
        new_reminder = {
            "title": "Prueba de recordatorio",
            "description": "Recordatorio creado desde script de prueba",
            "date": date.today().strftime("%Y-%m-%d"),
            "time": "15:00:00",
            "type": "personal",
            "priority": "medium"
        }
        
        response = requests.post(
            f"{CALENDAR_URL}/reminders",
            json=new_reminder,
            headers=headers
        )
        if response.status_code == 200:
            print("✅ Recordatorio creado exitosamente")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Probar obtener entrevistas
    print("\n3. Probando GET /api/calendar/interviews...")
    try:
        response = requests.get(
            f"{CALENDAR_URL}/interviews?year={year}&month={month}",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Entrevistas obtenidas: {len(data.get('data', []))} registros")
            for interview in data.get('data', [])[:3]:  # Mostrar solo las primeras 3
                print(f"   - {interview.get('candidate_name')} ({interview.get('date')} {interview.get('time')})")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Probar obtener actividades
    print("\n4. Probando GET /api/calendar/activities...")
    try:
        response = requests.get(
            f"{CALENDAR_URL}/activities?year={year}&month={month}",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Actividades obtenidas: {len(data.get('data', []))} registros")
            for activity in data.get('data', [])[:3]:  # Mostrar solo las primeras 3
                print(f"   - {activity.get('description')} ({activity.get('type')})")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de endpoints del calendario...")
    
    # Iniciar sesión
    token = login()
    if not token:
        print("❌ No se pudo obtener el token de autenticación")
        return
    
    print("✅ Token obtenido exitosamente")
    
    # Probar endpoints
    test_calendar_endpoints(token)
    
    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    main()

