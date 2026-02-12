import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from cv_processing_service_v2 import cv_processing_service_v2
    print("✅ Servicio CVProcessingServiceV2 importado correctamente.")
except ImportError as e:
    print(f"❌ Error importando servicio: {e}")
    sys.exit(1)

def test_moonshot_integration():
    print("\n--- INICIANDO PRUEBA DE INTEGRACIÓN MOONSHOT AI ---")
    
    api_key = os.getenv('MOONSHOT_API_KEY')
    if not api_key:
        print("❌ Error: MOONSHOT_API_KEY no encontrada en variables de entorno.")
        return
    
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
    print(f"🔑 API Key detectada: {masked_key}")
    
    print(f"🔑 API Key detectada: {masked_key}")
    
    # 2. Prueba con NVIDIA API
    nvidia_base_url = "https://integrate.api.nvidia.com/v1"
    print(f"\nPROBANDO CONEXIÓN A NVIDIA API ({nvidia_base_url})...")
    
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        
        # Intentar listar modelos
        response = requests.get(f"{nvidia_base_url}/models", headers=headers)
        
        if response.status_code == 200:
            print("✅ Conexión exitosa. Modelos disponibles:")
            models = response.json().get('data', [])
            for m in models:
                # Filtrar solo 'moonshot' o 'kimi' si hay muchos
                if 'moonshot' in m['id'].lower() or 'kimi' in m['id'].lower():
                    print(f"  - {m['id']} (DETECTADO!)")
                else:
                    # Mostrar primeros 5 otros para contexto
                    pass
        else:
            print(f"❌ Error conectando a NVIDIA API ({response.status_code}): {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    # Prueba Chat Simple
    print("\nPROBANDO CHAT SIMPLE (Ping)...")
    try:
        url = f"{nvidia_base_url}/chat/completions"
        data = {
            "model": "moonshotai/kimi-k2.5",
            "messages": [{"role": "user", "content": "Hola, responde solo 'Si' si me escuchas."}],
            "temperature": 0.5,
            "max_tokens": 500,
            "stream": False
        }
        res = requests.post(url, headers=headers, json=data, timeout=30)
        if res.status_code == 200:
            print(f"✅ Respuesta recibida: {res.json()['choices'][0]['message']['content']}")
            print(f"📄 JSON completo: {res.json()}")
        else:
            print(f"❌ Error chat simple ({res.status_code}): {res.text}")
            return
    except Exception as e:
        print(f"❌ Excepción chat simple: {e}")
        return

    print("\nPROBANDO PROCESAMIENTO DE TEXTO (Kimi-k2.5 - CV Completo)...")
    
    # CV de prueba simplificado
    dummy_cv_text = """
    JUAN PÉREZ
    Desarrollador Python Senior
    Ciudad de México, México
    Email: juan.perez@example.com
    Tel: +52 55 1234 5678
    
    EXPERIENCIA
    Tech Solutions Inc. - Desarrollador Backend (2020 - Actualidad)
    - Desarrollo de APIs REST con Flask y Django.
    - Optimización de consultas SQL.
    
    EDUCACIÓN
    Ingeniería en Sistemas - UNAM (2015-2019)
    
    HABILIDADES
    Python, SQL, Docker, AWS
    """
    
    try:
        result = cv_processing_service_v2.process_cv_text(dummy_cv_text, tenant_id=1)
        
        if result['success']:
            print("✅ ÉXITO: Moonshot AI procesó el CV correctamente.")
            print("\nDATOS EXTRAÍDOS:")
            import json
            print(json.dumps(result['data'], indent=2, ensure_ascii=False))
        else:
            print(f"❌ FALLO: Error al procesar CV: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {str(e)}")

if __name__ == "__main__":
    test_moonshot_integration()
