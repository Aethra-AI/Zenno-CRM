#!/usr/bin/env python3
"""
Script de prueba para verificar que el endpoint /api/dashboard/metrics funciona correctamente
"""

import requests
import json

def test_dashboard_metrics():
    """Probar el endpoint de métricas del dashboard"""
    
    # URL del endpoint
    url = "https://149.130.160.182.sslip.io/api/dashboard/metrics"
    
    # Token de autenticación (reemplazar con un token válido)
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNybS5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwicGVybWlzb3MiOnsiYWxsIjp0cnVlfSwidGVuYW50X2lkIjoxLCJjbGllbnRlX2lkIjpudWxsLCJjbGllbnRlX25vbWJyZSI6IkVtcHJlc2EgRGVtbyIsImV4cCI6MTc1OTgyMjgzMywianRpIjoiZjRjZGNiOGMtNDNlOS00ZThkLTgzZjQtYWY2Nzg3MGZhMGMyIn0.F077jPBH-auxDyg7tI_l7ky2C-Y4fuLnlQft2c7do9c"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("🧪 Probando endpoint /api/dashboard/metrics...")
        print(f"URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Éxito! Respuesta recibida:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Verificar campos esperados
            if data.get('success') and data.get('data'):
                required_fields = [
                    'total_candidatos',
                    'candidatos_hoy', 
                    'vacantes_por_estado',
                    'tasa_conversion',
                    'candidatos_por_mes',
                    'top_clientes',
                    'efectividad_usuario',
                    'tasa_exito_vacantes',
                    'candidatos_mas_activos',
                    'skills_demandados',
                    'distribucion_ciudades',
                    'usuarios_efectividad'
                ]
                
                missing_fields = []
                for field in required_fields:
                    if field not in data['data']:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"⚠️  Campos faltantes: {missing_fields}")
                else:
                    print("✅ Todos los campos requeridos están presentes")
                    
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_dashboard_metrics()
