"""
Servicio de procesamiento de CVs con Gemini AI
"""
from typing import Union, Dict, List, Any
import os
import json
import logging
from typing import Dict, Any, Optional, List
from io import BytesIO
from datetime import datetime
import concurrent.futures
import time
from threading import Lock

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

class CVProcessingService:
    """Servicio para procesar CVs con Gemini AI usando múltiples APIs"""
    
    def __init__(self):
        """Inicializar servicio de procesamiento con múltiples APIs"""
        
        # Verificar dependencias
        if not REQUESTS_AVAILABLE:
            logger.error("Módulo 'requests' no disponible. El servicio no funcionará correctamente.")
            raise ImportError("Módulo 'requests' requerido para el servicio de procesamiento de CVs")
        
        if not PyPDF2:
            logger.warning("Módulo 'PyPDF2' no disponible. No se podrán procesar archivos PDF.")
        
        if not docx:
            logger.warning("Módulo 'python-docx' no disponible. No se podrán procesar archivos DOCX.")
        
        # Obtener las APIs de Gemini disponibles
        self.gemini_api_keys = [
            os.getenv('GEMINI_API_KEY_1'),
            os.getenv('GEMINI_API_KEY_2'),
            os.getenv('GEMINI_API_KEY_3')
        ]
        
        # Filtrar APIs válidas
        self.gemini_api_keys = [key for key in self.gemini_api_keys if key]
        
        # Usar el modelo gemini-2.0-flash
        self.gemini_api_url = os.getenv('GEMINI_API_URL', 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent')
        
        # Rate limiting: 60 peticiones por minuto por API (Gemini 2.0 Flash)
        self.rate_limit_per_api = 60
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
            
            # Prompt mejorado para Gemini 2.0 Flash
            prompt = f"""
            Eres un asistente experto en análisis de CVs. Tu tarea es extraer información del siguiente CV y devolverla en formato JSON válido.
            
            INSTRUCCIONES:
            1. Analiza cuidadosamente TODO el contenido del CV
            2. Extrae TODA la información relevante
            3. Sigue ESTRICTAMENTE el esquema JSON proporcionado
            4. Si un campo no aplica, usa null
            5. No incluyas ningún texto fuera del JSON
            
            ESQUEMA REQUERIDO:
            {json.dumps({
                "personal_info": {
                    "nombre_completo": "string | null",
                    "email": "string | null",
                    "telefono": "string | null",
                    "ciudad": "string | null",
                    "pais": "string | null"
                },
                "experiencia": [{
                    "empresa": "string",
                    "puesto": "string",
                    "fecha_inicio": "string (YYYY-MM-DD)",
                    "fecha_fin": "string (YYYY-MM-DD o 'actual')",
                    "descripcion": "string",
                    "habilidades": ["string"]
                }],
                "educacion": [{
                    "institucion": "string",
                    "titulo": "string",
                    "fecha_inicio": "string (YYYY-MM-DD)",
                    "fecha_fin": "string (YYYY-MM-DD)",
                    "grado": "string"
                }],
                "habilidades": {
                    "tecnicas": ["string"],
                    "blandas": ["string"],
                    "idiomas": [{
                        "idioma": "string",
                        "nivel": "string (básico/intermedio/avanzado/nativo)"
                    }]
                },
                "resumen": "string"
            }, indent=2, ensure_ascii=False)}
            
            CV A ANALIZAR:
            {cv_text}
            
            IMPORTANTE: Devuelve SOLO el JSON válido, sin texto adicional.
            """
            
            # Preparar request para Gemini
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.1,  # Más determinista
                    "topP": 0.9,
                    "topK": 40,
                    "maxOutputTokens": 4096,
                    "responseMimeType": "application/json"
                }
            }
            
            # Llamar a Gemini API
            response = requests.post(
                f"{self.gemini_api_url}?key={selected_api_key}",
                headers=headers,
                json=data,
                timeout=120
            )
            
            if response.status_code != 200:
                error_msg = f"Error en Gemini API ({response.status_code}): {response.text}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
            
            # Procesar respuesta
            try:
                gemini_response = response.json()
                
                if 'candidates' not in gemini_response or not gemini_response['candidates']:
                    raise ValueError("Respuesta de Gemini no contiene candidatos")
                
                candidate = gemini_response['candidates'][0]
                if 'content' not in candidate or 'parts' not in candidate['content']:
                    raise ValueError("Formato de respuesta inválido de Gemini")
                
                response_text = candidate['content']['parts'][0]['text']
                
                # Limpiar respuesta
                response_text = response_text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:-3].strip()
                elif response_text.startswith('```'):
                    response_text = response_text[3:-3].strip()
                
                # Validar y parsear JSON
                try:
                    structured_data = json.loads(response_text)
                    
                    # Validar estructura básica
                    required_sections = ['personal_info', 'experiencia', 'educacion', 'habilidades']
                    if not all(section in structured_data for section in required_sections):
                        raise ValueError("Faltan secciones requeridas en la respuesta")
                    
                    logger.info("CV procesado exitosamente con Gemini 2.0 Flash")
                    
                    return {
                        'success': True,
                        'data': structured_data,
                        'raw_response': response_text
                    }
                    
                except json.JSONDecodeError as e:
                    error_msg = f"Error parseando JSON de Gemini: {str(e)}\nRespuesta: {response_text[:500]}..."
                    logger.error(error_msg)
                    return {
                        'success': False,
                        'error': error_msg
                    }
                    
            except Exception as e:
                error_msg = f"Error procesando respuesta de Gemini: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return {
                    'success': False,
                    'error': error_msg
                }
            
        except Exception as e:
            logger.error(f"Error procesando CV con Gemini: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_skills_summary(self, cv_data: Dict[str, Any]) -> str:
        """
        Extraer y consolidar todas las habilidades en una cadena separada por comas
        para facilitar búsquedas en el motor de búsqueda
        
        Args:
            cv_data: Datos del CV procesados
            
        Returns:
            String con todas las habilidades separadas por comas
        """
        skills_list = []
        
        try:
            habilidades = cv_data.get('habilidades', {})
            
            # Extraer de cada categoría
            if isinstance(habilidades, dict):
                # Habilidades técnicas
                if 'tecnicas' in habilidades and isinstance(habilidades['tecnicas'], list):
                    skills_list.extend(habilidades['tecnicas'])
                
                # Software Office
                if 'software_office' in habilidades and isinstance(habilidades['software_office'], list):
                    skills_list.extend(habilidades['software_office'])
                
                # Software empresarial
                if 'software_empresarial' in habilidades and isinstance(habilidades['software_empresarial'], list):
                    skills_list.extend(habilidades['software_empresarial'])
                
                # Herramientas especializadas
                if 'herramientas_especializadas' in habilidades and isinstance(habilidades['herramientas_especializadas'], list):
                    skills_list.extend(habilidades['herramientas_especializadas'])
                
                # Sistemas de gestión
                if 'sistemas_gestion' in habilidades and isinstance(habilidades['sistemas_gestion'], list):
                    skills_list.extend(habilidades['sistemas_gestion'])
                
                # Tecnologías de programación
                if 'tecnologias_programacion' in habilidades and isinstance(habilidades['tecnologias_programacion'], list):
                    skills_list.extend(habilidades['tecnologias_programacion'])
                
                # Bases de datos
                if 'bases_datos' in habilidades and isinstance(habilidades['bases_datos'], list):
                    skills_list.extend(habilidades['bases_datos'])
                
                # Metodologías
                if 'metodologias' in habilidades and isinstance(habilidades['metodologias'], list):
                    skills_list.extend(habilidades['metodologias'])
                
                # Habilidades blandas
                if 'blandas' in habilidades and isinstance(habilidades['blandas'], list):
                    skills_list.extend(habilidades['blandas'])
                
                # Habilidades extraídas de experiencia
                if 'habilidades_extraidas_experiencia' in habilidades and isinstance(habilidades['habilidades_extraidas_experiencia'], list):
                    skills_list.extend(habilidades['habilidades_extraidas_experiencia'])
                
                # Competencias profesionales
                if 'competencias_profesionales' in habilidades and isinstance(habilidades['competencias_profesionales'], list):
                    skills_list.extend(habilidades['competencias_profesionales'])
                
                # Idiomas
                if 'idiomas' in habilidades and isinstance(habilidades['idiomas'], list):
                    for idioma in habilidades['idiomas']:
                        if isinstance(idioma, dict) and 'idioma' in idioma:
                            nivel = idioma.get('nivel_oral', idioma.get('nivel_escrito', ''))
                            skills_list.append(f"{idioma['idioma']} ({nivel})" if nivel else idioma['idioma'])
            
            # Extraer tecnologías de experiencia detallada
            experiencia = cv_data.get('experiencia', {})
            if isinstance(experiencia, dict) and 'experiencia_detallada' in experiencia:
                for exp in experiencia['experiencia_detallada']:
                    if isinstance(exp, dict):
                        # Tecnologías
                        if 'tecnologias' in exp and isinstance(exp['tecnologias'], list):
                            skills_list.extend(exp['tecnologias'])
                        # Herramientas
                        if 'herramientas' in exp and isinstance(exp['herramientas'], list):
                            skills_list.extend(exp['herramientas'])
            
            # Limpiar y deduplicar
            skills_list = [skill.strip() for skill in skills_list if skill and isinstance(skill, str) and skill.strip()]
            skills_list = list(set(skills_list))  # Eliminar duplicados
            skills_list.sort()  # Ordenar alfabéticamente
            
            return ', '.join(skills_list)
            
        except Exception as e:
            logger.error(f"Error extrayendo resumen de habilidades: {str(e)}")
            return ''
    
    def validate_cv_data(self, cv_data: Union[Dict[str, Any], List[Any]]) -> Dict[str, Any]:
        """
        Validar y limpiar datos del CV
        
        Args:
            cv_data: Datos del CV procesados por Gemini (puede ser dict o list)
            
        Returns:
            Dict con datos validados y limpiados
        """
        try:
            # Si es una lista, convertir a diccionario con estructura esperada
            if isinstance(cv_data, list):
                logger.warning("Se recibió una lista en lugar de un diccionario, convirtiendo...")
                cv_data = {
                    'personal_info': {},
                    'experiencia': [],
                    'educacion': [],
                    'habilidades': {
                        'tecnicas': [],
                        'blandas': [],
                        'idiomas': []
                    }
                }
            
            validated_data = cv_data.copy()
            
            # Asegurar estructura básica
            if 'personal_info' not in validated_data:
                validated_data['personal_info'] = {}
            
            if 'experiencia' not in validated_data:
                validated_data['experiencia'] = []
            elif not isinstance(validated_data['experiencia'], list):
                validated_data['experiencia'] = []
            
            if 'educacion' not in validated_data:
                validated_data['educacion'] = []
            elif not isinstance(validated_data['educacion'], list):
                validated_data['educacion'] = []
            
            if 'habilidades' not in validated_data:
                validated_data['habilidades'] = {
                    'tecnicas': [],
                    'blandas': [],
                    'idiomas': []
                }
            
            # Validar información personal
            personal = validated_data['personal_info']
            if not isinstance(personal, dict):
                personal = {}
                validated_data['personal_info'] = personal
            
            # Validar email
            if personal.get('email') and not isinstance(personal['email'], str):
                personal['email'] = None
            elif personal.get('email') and '@' not in personal['email']:
                personal['email'] = None
            
            # Limpiar teléfono
            if personal.get('telefono'):
                if not isinstance(personal['telefono'], str):
                    personal['telefono'] = str(personal['telefono'])
                phone = ''.join(filter(str.isdigit, personal['telefono']))
                if len(phone) < 7:
                    personal['telefono'] = None
                else:
                    personal['telefono'] = phone
            
            # Validar experiencia
            if 'años_experiencia' in validated_data and validated_data['años_experiencia'] is not None:
                try:
                    validated_data['años_experiencia'] = float(validated_data['años_experiencia'])
                except (ValueError, TypeError):
                    validated_data['años_experiencia'] = 0
            
            # Validar habilidades
            if 'habilidades' not in validated_data or not isinstance(validated_data['habilidades'], dict):
                validated_data['habilidades'] = {
                    'tecnicas': [],
                    'blandas': [],
                    'idiomas': []
                }
            
            skills = validated_data['habilidades']
            
            # Asegurar que las listas de habilidades existan y sean listas
            for skill_type in ['tecnicas', 'blandas', 'idiomas']:
                if skill_type not in skills or not isinstance(skills[skill_type], list):
                    skills[skill_type] = []
                
                # Filtrar elementos no string
                skills[skill_type] = [
                    str(skill) for skill in skills[skill_type] 
                    if skill and (isinstance(skill, str) or isinstance(skill, (int, float)))
                ]
            
            logger.info("Validación de datos de CV completada exitosamente")
            
            return {
                'success': True,
                'validated_data': validated_data
            }
            
        except Exception as e:
            error_msg = f"Error validando datos del CV: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'raw_data': str(cv_data)[:500]  # Incluir parte de los datos para depuración
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
        
        # Validar que hay APIs disponibles
        if not self.gemini_api_keys:
            logger.error("No hay APIs de Gemini configuradas para procesamiento en lote")
            return [{'success': False, 'error': 'No hay APIs de Gemini configuradas'} for _ in cv_texts]
        
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

# Instancia global del servicio (solo si las dependencias están disponibles)
try:
    cv_processing_service = CVProcessingService()
except ImportError as e:
    logger.error(f"No se pudo inicializar el servicio de procesamiento: {e}")
    cv_processing_service = None

