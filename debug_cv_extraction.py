#!/usr/bin/env python3
"""
Script para debuggear la extracción de datos de CVs
"""

import os
import json
import asyncio
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from cv_processor import CVProcessor
from cv_data_completer import create_data_completer

async def debug_cv_extraction():
    """Debuggear extracción de CVs"""
    
    # Crear procesador
    processor = CVProcessor()
    
    # Archivos de prueba
    test_files = [
        "temp_uploads/1_1_0_CV_Alexa_Gisselle_Sanchez_Miranda_-_copia.pdf",
        "temp_uploads/1_1_2_karen_flores_cv.docx"
    ]
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"❌ Archivo no encontrado: {file_path}")
            continue
            
        print(f"\n🔍 Analizando: {file_path}")
        print("=" * 60)
        
        try:
            # 1. Extraer texto del archivo
            print("📄 Extrayendo texto...")
            text = processor.extract_text_from_file(file_path, file_path.split('.')[-1])
            print(f"📝 Texto extraído ({len(text)} caracteres):")
            print("-" * 40)
            print(text[:500] + "..." if len(text) > 500 else text)
            print("-" * 40)
            
            # 2. Procesar con IA
            print("\n🤖 Procesando con IA...")
            candidate_data = await processor.extract_candidate_data(text, file_path)
            
            print("📊 Datos extraídos por IA:")
            print(json.dumps(candidate_data, indent=2, ensure_ascii=False))
            
            # 3. Verificar campos críticos
            print("\n🔍 Verificación de campos críticos:")
            print(f"  - nombre_completo: {candidate_data.get('nombre_completo', 'NULL')}")
            print(f"  - email: {candidate_data.get('email', 'NULL')}")
            print(f"  - telefono: {candidate_data.get('telefono', 'NULL')}")
            
            # 4. Completar datos faltantes
            print("\n🔧 Completando datos faltantes...")
            data_completer = create_data_completer()
            completed_data = data_completer.complete_missing_data(candidate_data, text)
            
            print("📊 Datos después de completar:")
            print(json.dumps(completed_data, indent=2, ensure_ascii=False))
            
            # 5. Validar datos finales
            print("\n✅ Validación final:")
            is_valid, errors = data_completer.validate_completed_data(completed_data)
            print(f"  - Válido: {is_valid}")
            print(f"  - Errores: {errors}")
            
        except Exception as e:
            print(f"❌ Error procesando {file_path}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_cv_extraction())
