import requests
import base64
import os
import io
from reportlab.pdfgen import canvas

# 1. GENERAR PDF DUMMY QUE CONTENGA TEXTO
def create_dummy_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "HOLA KIMI, ESTO ES UNA PRUEBA DE PDF. EL CODIGO SECRETO ES: PDF-999")
    c.save()
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# 2. PROBAR API CON PDF
def test_pdf_vision():
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        print("❌ Error: MOONSHOT_API_KEY no encontrada")
        return

    base_url = "https://integrate.api.nvidia.com/v1"
    
    print("� Generando PDF de prueba...")
    b64_pdf = create_dummy_pdf()
    print(f"✅ PDF generado ({len(b64_pdf)} bytes base64)")

    # Intentar enviar PDF como si fuera una imagen o archivo
    # Probaremos varios formatos si el primero falla
    # 1. Como image_url con mime application/pdf (a veces funciona en algunos modelos multimodales)
    
    payload = {
        "model": "moonshotai/kimi-k2.5",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analiza este documento PDF. Qué dice?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:application/pdf;base64,{b64_pdf}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1024,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    print("\n🚀 Enviando a NVIDIA API (Kimi-k2.5 PDF)...")
    try:
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=60)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 Response Text: {response.text}")
        
    except Exception as e:
        print(f"\n❌ EXCEPCIÓN: {str(e)}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_pdf_vision()
