import os
import sys
import logging
from reportlab.pdfgen import canvas
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

from cv_processing_service_v2 import CVProcessingServiceV2

# Configurar logging para ver lo que pasa
logging.basicConfig(level=logging.INFO)

def create_valid_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    # Escribir texto grande y claro que Kimi pueda leer en la imagen
    c.setFont("Helvetica", 24)
    c.drawString(100, 700, "CURRICULUM VITAE TEST")
    c.drawString(100, 650, "Nombre: Juan Perez Scanned")
    c.drawString(100, 600, "Email: juan.perez@test.com")
    c.drawString(100, 550, "Experiencia: Desarrollador Python Senior")
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def test_scanned_pdf_fallback():
    print("🚀 Iniciando prueba de fallback para PDF Escaneado...")
    
    # 1. Crear servicio
    service = CVProcessingServiceV2()
    
    # 2. Crear PDF dummy
    pdf_content = create_valid_pdf()
    print(f"📄 PDF generado ({len(pdf_content)} bytes)")
    
    # 3. MOCK: Forzar que extract_text devuelva vacío para simular que es escaneado
    # Guardamos la referencia original para restaurarla si fuera necesario
    original_extract = service.extract_text_from_file
    service.extract_text_from_file = lambda content, name: "" 
    print("🕵️  Mock activado: Simular extracción de texto fallida (PDF escaneado)")
    
    # 4. Procesar
    try:
        result = service.process_cv_with_kimi(pdf_content, "test_scanned.pdf", 1)
        
        print("\n📊 RESULTADO:")
        print(result)
        
        if result.get('success'):
            data = result.get('data', {})
            name = data.get('personal_info', {}).get('nombre_completo')
            print(f"\n✅ NOMBRE DETECTADO: {name}")
            
            if "Juan Perez" in str(name):
                print("🎉 PRUEBA EXITOSA: Kimi leyó el PDF como imagen!")
            else:
                print("⚠️  Kimi respondió pero no leyó el nombre esperado.")
        else:
            print(f"❌ FALLÓ: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {e}")

if __name__ == "__main__":
    test_scanned_pdf_fallback()
