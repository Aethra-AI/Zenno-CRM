"""
Servicio de procesamiento de CVs con NVIDIA API (Moonshot Model)
"""
from typing import Union, Dict, List, Any, Optional
import os
import json
import logging
import time
from pathlib import Path
from io import BytesIO

# Imports opcionales
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False

# PDF y DOCX processing
try:
    import PyPDF2
    import docx
    from docx import Document
except ImportError:
    PyPDF2 = None
    docx = None
    Document = None

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CVProcessingServiceV2:
    """Servicio para procesar CVs con NVIDIA API (Moonshot/Kimi)"""
    
    def __init__(self):
        """Inicializar servicio de procesamiento con NVIDIA API"""
        
        # Verificar dependencias
        if not REQUESTS_AVAILABLE:
            logger.error("Módulo 'requests' no disponible. El servicio no funcionará correctamente.")
            raise ImportError("Módulo 'requests' requerido para el servicio de procesamiento de CVs")
        
        # Obtener API Key de Moonshot (usada para NVIDIA)
        self.moonshot_api_key = os.getenv('MOONSHOT_API_KEY')
        
        if not self.moonshot_api_key:
            logger.warning("No se encontró MOONSHOT_API_KEY en variables de entorno")
        else:
            logger.info("Inicializado servicio con NVIDIA API (Moonshot/Kimi)")
            
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "moonshotai/kimi-k2.5"  # Modelo en NVIDIA API Catalog
        
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extraer texto de archivo PDF"""
        try:
            if not PyPDF2:
                # Fallback básico si no hay PyPDF2
                return ""
            
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extrayendo texto de PDF: {str(e)}")
            return ""

    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extraer texto de archivo DOCX"""
        try:
            if not docx:
                return ""
            
            doc = Document(BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extrayendo texto de DOCX: {str(e)}")
            return ""

    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """Extraer texto de archivo según su tipo"""
        try:
            filename_lower = filename.lower()
            if filename_lower.endswith('.pdf'):
                return self.extract_text_from_pdf(file_content)
            elif filename_lower.endswith('.docx') or filename_lower.endswith('.doc'):
                return self.extract_text_from_docx(file_content)
            else:
                try:
                    return file_content.decode('utf-8')
                except:
                    return file_content.decode('latin-1')
        except Exception as e:
            logger.error(f"Error extrayendo texto del archivo {filename}: {str(e)}")
            return ""

    def process_cv_with_kimi(self, file_content: bytes, filename: str, tenant_id: int) -> Dict[str, Any]:
        """
        Procesar CV completo extrayendo texto localmente y enviando a NVIDIA API
        """
        if not self.moonshot_api_key:
            return {'success': False, 'error': 'MOONSHOT_API_KEY no configurada'}
            
        filename_lower = filename.lower()
        is_image = filename_lower.endswith(('.jpg', '.jpeg', '.png', '.webp'))
        
        # 1. Si es IMAGEN directa
        if is_image:
            try:
                import base64
                b64_image = base64.b64encode(file_content).decode('utf-8')
                return self.process_cv_images([b64_image], tenant_id)
            except Exception as e:
                return {'success': False, 'error': f"Error procesando imagen: {str(e)}"}
        
        # 2. Si es PDF/DOC: Intentar extracción de texto
        cv_text = self.extract_text_from_file(file_content, filename)
        
        # 3. Si hay texto suficiente -> Procesar como Texto
        if cv_text and len(cv_text.strip()) >= 50:
            return self.process_cv_text(cv_text, tenant_id)
            
        # 4. Fallback: Si es PDF con poco texto (escaneado) -> Convertir a imágenes y usar Visión
        if filename_lower.endswith('.pdf'):
            logger.info(f"Texto insuficiente ({len(cv_text)} chars). Intentando OCR visual para {filename}...")
            try:
                images = self._convert_pdf_to_images(file_content)
                if images:
                    return self.process_cv_images(images, tenant_id)
            except Exception as e:
                logger.error(f"Fallo en conversión PDF a Imagen: {e}")
        
        return {
            'success': False,
            'error': 'No se pudo extraer texto suficiente ni procesar como imagen (posible PDF vacío o encriptado).'
        }

    def _convert_pdf_to_images(self, file_content: bytes) -> List[str]:
        """Convertir páginas de PDF a lista de imágenes base64 (máx 3 páginas)"""
        images_b64 = []
        try:
            import fitz  # PyMuPDF
            import base64
            
            doc = fitz.open(stream=file_content, filetype="pdf")
            # Limitar a las primeras 3 páginas para no saturar el contexto
            for i in range(min(len(doc), 3)):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Zoom 2x para mejor calidad
                img_data = pix.tobytes("png")
                b64_str = base64.b64encode(img_data).decode('utf-8')
                images_b64.append(b64_str)
                
            doc.close()
            return images_b64
        except ImportError:
            logger.error("PyMuPDF (fitz) no instalado. No se puede realizar OCR visual.")
            return []
        except Exception as e:
            logger.error(f"Error convirtiendo PDF a imágenes: {e}")
            return []

    def process_cv_images(self, b64_images: List[str], tenant_id: int) -> Dict[str, Any]:
        """
        Procesar CV (lista de imágenes base64) usando Visión
        """
        if not self.moonshot_api_key or not b64_images:
            return {'success': False, 'error': 'Datos insuficientes para procesar'}
            
        try:
            prompt = """
            Eres un experto en Recursos Humanos. Analiza estas IMAGENES de un CV (pueden ser varias páginas) y extrae la información en JSON estricto.
            Si es un documento escaneado, transcríbelo con cuidado.
            
            INSTRUCCIONES:
            1. Transcribe y estructura TODA la información visible.
            2. Usa null para datos faltantes.
            3. Devuelve SOLO JSON válido.
            
            ESQUEMA JSON:
            {
                "personal_info": { "nombre_completo": "string", "email": "string", "telefono": "string", "ciudad": "string", "pais": "string" },
                "experiencia": [ { "empresa": "string", "puesto": "string", "fecha_inicio": "string", "fecha_fin": "string", "descripcion": "string", "habilidades": ["string"] } ],
                "educacion": [ { "institucion": "string", "titulo": "string", "fecha_inicio": "string", "fecha_fin": "string", "grado": "string" } ],
                "habilidades": { "tecnicas": [], "blandas": [], "idiomas": [{ "idioma": "string", "nivel": "string" }] },
                "resumen": "string"
            }
            """
            
            # Construir contenido multimodal
            content_list = [{"type": "text", "text": prompt}]
            
            for b64 in b64_images:
                content_list.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}
                })

            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.moonshot_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": content_list}],
                "temperature": 0.2,
                "max_tokens": 4096,
                "stream": False
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message'].get('content', '')
                
                if not content:
                    return {'success': False, 'error': f"Respuesta vacía de Vision API. Finish reason: {result['choices'][0]['finish_reason']}"}
                
                # Limpiar markdown
                content = content.replace("```json", "").replace("```", "").strip()
                
                try:
                    extracted_data = json.loads(content)
                    return {'success': True, 'data': extracted_data}
                except json.JSONDecodeError:
                    return {'success': False, 'error': f"Error parseando JSON de imagen: {content[:100]}..."}
            else:
                return {'success': False, 'error': f"Error NVIDIA Vision API ({response.status_code}): {response.text}"}
                
        except Exception as e:
            logger.error(f"Error procesando imágenes con Kimi: {str(e)}")
            return {'success': False, 'error': str(e)}


    def validate_cv_data(self, cv_data: Union[Dict[str, Any], List[Any]]) -> Dict[str, Any]:
        """
        Validar y limpiar datos del CV (Reutilizado del servicio anterior)
        """
        # ... (Mantener lógica de validación original para consistencia) ...
        # Por simplicidad, copio la logica basica aquí o se podría heredar
        
        try:
             # Si es una lista, convertir a diccionario con estructura esperada
            if isinstance(cv_data, list):
                cv_data = {
                    'personal_info': {},
                    'experiencia': [],
                    'educacion': [],
                    'habilidades': {'tecnicas': [], 'blandas': [], 'idiomas': []}
                }
            
            validated_data = cv_data.copy()
            
            # Asegurar estructura básica
            for key, default in [
                ('personal_info', {}),
                ('experiencia', []),
                ('educacion', []),
                ('habilidades', {'tecnicas': [], 'blandas': [], 'idiomas': []})
            ]:
                if key not in validated_data:
                    validated_data[key] = default
            
            # Asegurar que experiencia tenga campos mínimos para evitar el bug "por definir"
            if isinstance(validated_data['experiencia'], list):
                for exp in validated_data['experiencia']:
                    if not exp.get('puesto'): exp['puesto'] = "Posición no especificada"
                    if not exp.get('empresa'): exp['empresa'] = "Empresa no especificada"

            return {
                'success': True,
                'validated_data': validated_data
            }
        except Exception as e:
             return {'success': False, 'error': str(e)}

    def extract_skills_summary(self, cv_data: Dict[str, Any]) -> str:
        """Extraer resumen de habilidades (Reutilizado)"""
        skills_list = []
        habilidades = cv_data.get('habilidades', {})
        if isinstance(habilidades, dict):
            for key in ['tecnicas', 'blandas']:
                if key in habilidades and isinstance(habilidades[key], list):
                    skills_list.extend(habilidades[key])
            if 'idiomas' in habilidades and isinstance(habilidades['idiomas'], list):
                for idioma in habilidades['idiomas']:
                     if isinstance(idioma, dict):
                         skills_list.append(idioma.get('idioma', ''))
        
        return ", ".join(filter(None, skills_list))


# Instancia global
try:
    cv_processing_service_v2 = CVProcessingServiceV2()
except Exception as e:
    logger.error(f"No se pudo inicializar servicio V2: {e}")
    cv_processing_service_v2 = None

