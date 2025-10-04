#!/usr/bin/env python3
"""
Script para verificar las API keys de Gemini
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv()

def test_gemini_keys():
    """Probar las API keys de Gemini"""
    print("🔍 Verificando API keys de Gemini...")
    
    # Obtener las 3 API keys
    keys = [
        os.getenv('GEMINI_API_KEY_1'),
        os.getenv('GEMINI_API_KEY_2'), 
        os.getenv('GEMINI_API_KEY_3')
    ]
    
    print(f"📋 API Keys encontradas: {sum(1 for key in keys if key)}/3")
    
    for i, key in enumerate(keys, 1):
        if not key:
            print(f"❌ GEMINI_API_KEY_{i}: No configurada")
            continue
            
        print(f"🔑 GEMINI_API_KEY_{i}: {key[:10]}...{key[-4:]}")
        
        try:
            # Configurar la API key
            genai.configure(api_key=key)
            
            # Probar con un modelo simple
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Hacer una prueba simple
            response = model.generate_content("Hola, ¿funcionas?")
            
            if response.text:
                print(f"✅ GEMINI_API_KEY_{i}: FUNCIONA - {response.text[:50]}...")
            else:
                print(f"❌ GEMINI_API_KEY_{i}: No responde")
                
        except Exception as e:
            print(f"❌ GEMINI_API_KEY_{i}: ERROR - {str(e)[:100]}...")
    
    print("\n🔍 Verificando modelos disponibles...")
    
    try:
        # Probar con la primera key válida
        valid_key = next((key for key in keys if key), None)
        if valid_key:
            genai.configure(api_key=valid_key)
            
            # Listar modelos disponibles
            models = list(genai.list_models())
            print(f"📋 Modelos disponibles: {len(models)}")
            
            for model in models[:5]:  # Mostrar solo los primeros 5
                print(f"  - {model.name}")
                
        else:
            print("❌ No hay API keys válidas para verificar modelos")
            
    except Exception as e:
        print(f"❌ Error verificando modelos: {e}")

if __name__ == "__main__":
    test_gemini_keys()
