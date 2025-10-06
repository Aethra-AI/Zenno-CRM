"""
Servicio de procesamiento de CVs con Gemini AI
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
import requests
from io import BytesIO
from datetime import datetime

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

class CVProcessingService:
    """Servicio para procesar CVs con Gemini AI usando múltiples APIs"""
    
    def __init__(self):
        """Inicializar servicio de procesamiento con múltiples APIs"""
        # Obtener las 3 APIs de Gemini disponibles
        self.gemini_api_keys = [
            os.getenv('GEMINI_API_KEY_1'),
            os.getenv('GEMINI_API_KEY_2'),
            os.getenv('GEMINI_API_KEY_3')
        ]
        
        # Filtrar APIs válidas
        self.gemini_api_keys = [key for key in self.gemini_api_keys if key]
        
        self.gemini_api_url = os.getenv('GEMINI_API_URL', 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent')
        
        # Rate limiting: 15 peticiones por minuto por API (Gemini 2.5 Flash Lite)
        self.rate_limit_per_api = 15
        self.rate_limit_window = 60  # segundos
        
        if not self.gemini_api_keys:
            logger.warning("No se encontraron APIs de Gemini en variables de entorno")
        else:
            logger.info(f"Inicializado con {len(self.gemini_api_keys)} APIs de Gemini disponibles")
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """
        Extraer texto de archivo PDF
        
        Args:
            file_content: Contenido del archivo PDF
            
        Returns:
            str: Texto extraído
        """
        try:
            if not PyPDF2:
                raise ImportError("PyPDF2 no está instalado")
            
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extrayendo texto de PDF: {str(e)}")
            raise
    
    def extract_text_from_docx(self, file_content: bytes) -> str:
        """
        Extraer texto de archivo DOCX
        
        Args:
            file_content: Contenido del archivo DOCX
            
        Returns:
            str: Texto extraído
        """
        try:
            if not docx:
                raise ImportError("python-docx no está instalado")
            
            doc = Document(BytesIO(file_content))
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extrayendo texto de DOCX: {str(e)}")
            raise
    
    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """
        Extraer texto de archivo según su tipo
        
        Args:
            file_content: Contenido del archivo
            filename: Nombre del archivo
            
        Returns:
            str: Texto extraído
        """
        try:
            filename_lower = filename.lower()
            
            if filename_lower.endswith('.pdf'):
                return self.extract_text_from_pdf(file_content)
            elif filename_lower.endswith('.docx') or filename_lower.endswith('.doc'):
                return self.extract_text_from_docx(file_content)
            else:
                # Para otros tipos de archivo, intentar como texto plano
                try:
                    return file_content.decode('utf-8')
                except UnicodeDecodeError:
                    return file_content.decode('latin-1')
                    
        except Exception as e:
            logger.error(f"Error extrayendo texto del archivo {filename}: {str(e)}")
            raise
    
    def process_cv_with_gemini(self, cv_text: str, tenant_id: int, api_index: int = 0) -> Dict[str, Any]:
        """
        Procesar CV con Gemini AI para extraer información estructurada
        
        Args:
            cv_text: Texto del CV
            tenant_id: ID del tenant
            api_index: Índice de la API a usar (0, 1, 2)
            
        Returns:
            Dict con información estructurada del candidato
        """
        try:
            if not self.gemini_api_keys:
                raise ValueError("No hay APIs de Gemini configuradas")
            
            # Seleccionar API usando round-robin
            selected_api_key = self.gemini_api_keys[api_index % len(self.gemini_api_keys)]
            logger.info(f"Usando Gemini API {api_index % len(self.gemini_api_keys) + 1} para procesar CV")
            
            # Prompt para Gemini
            prompt = f"""
            Analiza el siguiente CV y extrae la información en formato JSON estructurado.
            El CV pertenece al tenant {tenant_id}.
            
            Por favor, extrae y estructura la siguiente información:
            
            {{
                "personal_info": {{
                    "nombre_completo": "string",
                    "email": "string",
                    "telefono": "string",
                    "ciudad": "string",
                    "pais": "string",
                    "fecha_nacimiento": "string (YYYY-MM-DD o null si no se encuentra)",
                    "linkedin": "string o null",
                    "github": "string o null"
                }},
                "experiencia": {{
                    "años_experiencia": "number",
                    "experiencia_detallada": [
                        {{
                            "empresa": "string",
                            "posicion": "string",
                            "fecha_inicio": "string (YYYY-MM-DD)",
                            "fecha_fin": "string (YYYY-MM-DD o 'actual' si está trabajando)",
                            "descripcion": "string",
                            "tecnologias": ["array de strings"]
                        }}
                    ]
                }},
                "educacion": [
                    {{
                        "institucion": "string",
                        "titulo": "string",
                        "fecha_inicio": "string (YYYY-MM-DD)",
                        "fecha_fin": "string (YYYY-MM-DD)",
                        "grado": "string"
                    }}
                ],
                "habilidades": {{
                    "tecnicas": ["array de strings"],
                    "blandas": ["array de strings"],
                    "idiomas": ["array de strings con nivel"]
                }},
                "certificaciones": [
                    {{
                        "nombre": "string",
                        "institucion": "string",
                        "fecha_obtencion": "string (YYYY-MM-DD)",
                        "vigencia": "string o null"
                    }}
                ],
                "resumen": "string (resumen profesional en 2-3 líneas)",
                "expectativas": {{
                    "salario_minimo": "number o null",
                    "salario_deseado": "number o null",
                    "tipo_trabajo": "string (remoto/presencial/hibrido)",
                    "disponibilidad": "string"
                }},
                "metadata": {{
                    "calidad_datos": "string (alta/media/baja)",
                    "completitud": "number (0-100)",
                    "confiabilidad": "string (alta/media/baja)",
                    "fecha_procesamiento": "{json.dumps(datetime.now().isoformat())}"
                }}
            }}
            
            IMPORTANTE:
            - Si no encuentras información específica, usa null
            - Para fechas, usa formato YYYY-MM-DD
            - Para números, usa solo el valor numérico
            - Asegúrate de que el JSON sea válido
            - El resumen debe ser conciso y profesional
            
            CV a analizar:
            {cv_text}
            """
            
            # Preparar request para Gemini
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 1,
                    "topP": 1
                }
            }
            
            # Llamar a Gemini API con la API seleccionada
            response = requests.post(
                f"{self.gemini_api_url}?key={selected_api_key}",
                headers=headers,
                json=data,
                timeout=120
            )
            
            if response.status_code != 200:
                logger.error(f"Error en Gemini API: {response.status_code} - {response.text}")
                raise Exception(f"Error en Gemini API: {response.status_code}")
            
            # Procesar respuesta
            gemini_response = response.json()
            
            if 'candidates' not in gemini_response or not gemini_response['candidates']:
                raise Exception("Respuesta inválida de Gemini API")
            
            # Extraer texto de la respuesta
            candidate = gemini_response['candidates'][0]
            if 'content' not in candidate or 'parts' not in candidate['content']:
                raise Exception("Formato de respuesta inválido de Gemini")
            
            response_text = candidate['content']['parts'][0]['text']
            
            # Limpiar y parsear JSON
            # Remover markdown code blocks si existen
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            # Parsear JSON
            try:
                structured_data = json.loads(response_text.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando JSON de Gemini: {str(e)}")
                logger.error(f"Respuesta raw: {response_text}")
                raise Exception(f"Error parseando respuesta de Gemini: {str(e)}")
            
            logger.info("CV procesado exitosamente con Gemini")
            
            return {
                'success': True,
                'data': structured_data,
                'raw_response': response_text
            }
            
        except Exception as e:
            logger.error(f"Error procesando CV con Gemini: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_cv_data(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar y limpiar datos del CV
        
        Args:
            cv_data: Datos del CV procesados por Gemini
            
        Returns:
            Dict con datos validados y limpiados
        """
        try:
            validated_data = cv_data.copy()
            
            # Validar información personal
            if 'personal_info' in validated_data:
                personal = validated_data['personal_info']
                
                # Validar email
                if personal.get('email') and '@' not in personal['email']:
                    personal['email'] = None
                
                # Limpiar teléfono
                if personal.get('telefono'):
                    phone = ''.join(filter(str.isdigit, personal['telefono']))
                    if len(phone) < 7:
                        personal['telefono'] = None
                    else:
                        personal['telefono'] = phone
            
            # Validar experiencia
            if 'experiencia' in validated_data:
                exp = validated_data['experiencia']
                
                # Asegurar que años_experiencia sea número
                if isinstance(exp.get('años_experiencia'), str):
                    try:
                        exp['años_experiencia'] = float(exp['años_experiencia'])
                    except ValueError:
                        exp['años_experiencia'] = 0
            
            # Validar habilidades
            if 'habilidades' in validated_data:
                skills = validated_data['habilidades']
                
                # Asegurar que sean arrays
                for skill_type in ['tecnicas', 'blandas', 'idiomas']:
                    if skill_type in skills and not isinstance(skills[skill_type], list):
                        skills[skill_type] = []
            
            return {
                'success': True,
                'validated_data': validated_data
            }
            
        except Exception as e:
            logger.error(f"Error validando datos del CV: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_cv_batch(self, cv_texts: List[str], tenant_id: int) -> List[Dict[str, Any]]:
        """
        Procesar lote de CVs con procesamiento paralelo entre múltiples APIs
        
        Args:
            cv_texts: Lista de textos de CVs
            tenant_id: ID del tenant
            
        Returns:
            Lista de resultados procesados
        """
        import concurrent.futures
        import time
        from threading import Lock
        
        results = [None] * len(cv_texts)  # Mantener orden original
        api_counters = {i: 0 for i in range(len(self.gemini_api_keys))}  # Contador por API
        counters_lock = Lock()
        
        def process_single_cv(index_and_text):
            index, cv_text = index_and_text
            
            try:
                # Usar round-robin para distribuir entre APIs
                with counters_lock:
                    api_index = index % len(self.gemini_api_keys)
                    api_counters[api_index] += 1
                    current_count = api_counters[api_index]
                
                logger.info(f"Procesando CV {index+1}/{len(cv_texts)} con API {api_index + 1} (petición #{current_count})")
                
                # Calcular delay basado en rate limiting (15 peticiones/minuto = 4 segundos entre peticiones)
                delay = (current_count - 1) * 4  # 0, 4, 8, 12... segundos
                if delay > 0:
                    time.sleep(delay)
                
                result = self.process_cv_with_gemini(cv_text, tenant_id, api_index)
                return index, result
                    
            except Exception as e:
                logger.error(f"Error procesando CV {index+1}: {str(e)}")
                return index, {
                    'success': False,
                    'error': str(e)
                }
        
        # Procesar en paralelo con ThreadPoolExecutor
        max_workers = min(len(self.gemini_api_keys), 3)  # Máximo 3 workers para 3 APIs
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Crear lista de tareas
            tasks = [(i, cv_text) for i, cv_text in enumerate(cv_texts)]
            
            # Ejecutar tareas en paralelo
            future_to_index = {executor.submit(process_single_cv, task): task[0] for task in tasks}
            
            # Recoger resultados
            for future in concurrent.futures.as_completed(future_to_index):
                index, result = future.result()
                results[index] = result
        
        return results

# Instancia global del servicio
cv_processing_service = CVProcessingService()

