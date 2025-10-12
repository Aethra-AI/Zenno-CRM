"""
Servicio de procesamiento de CVs con Gemini AI
"""
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
            
            # Prompt mejorado y robusto para Gemini
            prompt = f"""
            Eres un experto analista de CVs con especialización en extracción de datos estructurados para sistemas de reclutamiento.
            Tu tarea es analizar EXHAUSTIVAMENTE el siguiente CV y extraer TODA la información disponible en formato JSON estructurado.
            El CV pertenece al tenant {tenant_id}.
            
            INSTRUCCIONES CRÍTICAS PARA ANÁLISIS PROFUNDO:
            
            📋 LECTURA COMPLETA:
            - Lee TODO el contenido del CV palabra por palabra, no solo fragmentos
            - Analiza cada sección: experiencia, educación, habilidades, certificaciones, proyectos
            - Busca información implícita y explícita
            - Identifica patrones y contextos profesionales
            
            💼 EXPERIENCIA LABORAL:
            - Extrae TODAS las experiencias laborales sin omitir ninguna
            - Para cada trabajo, identifica:
              * Responsabilidades principales (todas las mencionadas)
              * Logros cuantificables (números, porcentajes, resultados)
              * Tecnologías y herramientas utilizadas (software, sistemas, plataformas)
              * Habilidades demostradas en ese rol
              * Contexto del trabajo (tamaño de equipo, industria, tipo de proyectos)
            
            🎯 EXTRACCIÓN INTELIGENTE DE HABILIDADES:
            - Extrae habilidades de MÚLTIPLES fuentes:
              1. Sección explícita de habilidades
              2. Descripciones de experiencia laboral (qué hacía, qué usaba)
              3. Proyectos mencionados (tecnologías aplicadas)
              4. Educación y certificaciones (conocimientos adquiridos)
              5. Logros y responsabilidades (competencias demostradas)
            
            - Identifica y extrae:
              * Software: Excel, Word, PowerPoint, Outlook, SAP, Salesforce, Oracle, etc.
              * Herramientas técnicas: Python, Java, SQL, JavaScript, React, etc.
              * Sistemas: ERP, CRM, POS, gestión de inventarios, etc.
              * Habilidades blandas: liderazgo, trabajo en equipo, comunicación, etc.
              * Idiomas: español, inglés, etc. con niveles
              * Certificaciones profesionales
            
            🔍 ANÁLISIS CONTEXTUAL:
            - Infiere habilidades del contexto:
              * Si fue "Gerente" → liderazgo, gestión de equipos, toma de decisiones
              * Si trabajó en "ventas" → negociación, atención al cliente, CRM
              * Si fue "analista" → análisis de datos, Excel, reportes
              * Si fue "desarrollador" → programación, frameworks, bases de datos
            
            📊 ESTRUCTURA Y DETALLE:
            - Cada experiencia debe tener descripción completa y detallada
            - Lista TODAS las tecnologías mencionadas (no resumas)
            - Separa habilidades técnicas de habilidades blandas
            - Identifica niveles de dominio cuando sea posible
            
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
                    "github": "string o null",
                    "portfolio": "string o null",
                    "sitio_web": "string o null"
                }},
                "experiencia": {{
                    "años_experiencia": "number (calculado desde la primera experiencia)",
                    "experiencia_detallada": [
                        {{
                            "empresa": "string",
                            "posicion": "string",
                            "fecha_inicio": "string (YYYY-MM-DD)",
                            "fecha_fin": "string (YYYY-MM-DD o 'actual' si está trabajando)",
                            "duracion_meses": "number",
                            "descripcion_completa": "string (descripción detallada de responsabilidades)",
                            "logros": ["array de strings con logros específicos"],
                            "tecnologias": ["array de strings con todas las tecnologías mencionadas"],
                            "herramientas": ["array de strings con herramientas usadas"],
                            "tamaño_empresa": "string (startup/pequeña/mediana/grande/empresa)",
                            "industria": "string",
                            "reportes_a": "string o null",
                            "equipo_a_cargo": "string o null"
                        }}
                    ],
                    "resumen_experiencia": "string (resumen de 3-4 líneas del perfil profesional)",
                    "especializaciones": ["array de strings con áreas de especialización"],
                    "logros_destacados": ["array de strings con logros más importantes"]
                }},
                "educacion": [
                    {{
                        "institucion": "string",
                        "titulo": "string",
                        "fecha_inicio": "string (YYYY-MM-DD)",
                        "fecha_fin": "string (YYYY-MM-DD)",
                        "grado": "string",
                        "estado": "string (completado/en_progreso)",
                        "promedio": "string o null",
                        "honores": "string o null"
                    }}
                ],
                "certificaciones": [
                    {{
                        "nombre": "string",
                        "institucion": "string",
                        "fecha_obtencion": "string (YYYY-MM-DD)",
                        "fecha_expiracion": "string (YYYY-MM-DD o null)",
                        "vigencia": "string o null",
                        "numero_certificado": "string o null",
                        "url": "string o null"
                    }}
                ],
                "cursos_formacion": [
                    {{
                        "nombre": "string",
                        "institucion": "string",
                        "fecha": "string (YYYY-MM-DD)",
                        "duracion": "string o null",
                        "estado": "string (completado/en_progreso)"
                    }}
                ],
                "habilidades": {{
                    "tecnicas": ["array de strings con habilidades técnicas específicas"],
                    "blandas": ["array de strings con habilidades blandas"],
                    "software_office": ["Excel, Word, PowerPoint, Outlook, Access, etc."],
                    "software_empresarial": ["SAP, Oracle, Salesforce, Microsoft Dynamics, etc."],
                    "herramientas_especializadas": ["AutoCAD, Photoshop, herramientas específicas del sector"],
                    "sistemas_gestion": ["ERP, CRM, POS, WMS, sistemas de inventario, etc."],
                    "tecnologias_programacion": ["Python, Java, JavaScript, C++, etc. si aplica"],
                    "bases_datos": ["SQL, MySQL, PostgreSQL, MongoDB, etc. si aplica"],
                    "metodologias": ["Agile, Scrum, Six Sigma, Lean, etc. si aplica"],
                    "idiomas": [
                        {{
                            "idioma": "string",
                            "nivel_escrito": "string (básico/intermedio/avanzado/nativo)",
                            "nivel_oral": "string (básico/intermedio/avanzado/nativo)",
                            "certificacion": "string o null"
                        }}
                    ],
                    "niveles_dominio": {{
                        "experto": ["tecnologías/herramientas donde tiene más de 5 años o dominio experto"],
                        "avanzado": ["tecnologías/herramientas con 3-5 años o nivel avanzado"],
                        "intermedio": ["tecnologías/herramientas con 1-3 años o nivel intermedio"],
                        "básico": ["tecnologías/herramientas con menos de 1 año o nivel básico"]
                    }},
                    "habilidades_extraidas_experiencia": ["TODAS las habilidades identificadas en descripciones de trabajo"],
                    "competencias_profesionales": ["gestión de proyectos, liderazgo de equipos, análisis financiero, etc."]
                }},
                "proyectos": [
                    {{
                        "nombre": "string",
                        "descripcion": "string",
                        "tecnologias": ["array de strings"],
                        "fecha": "string (YYYY-MM-DD o período)",
                        "url": "string o null",
                        "rol": "string"
                    }}
                ],
                "resumen": "string (resumen profesional detallado en 4-5 líneas)",
                "expectativas": {{
                    "salario_minimo": "number o null",
                    "salario_deseado": "number o null",
                    "tipo_trabajo": "string (remoto/presencial/hibrido)",
                    "disponibilidad": "string",
                    "ubicacion_preferida": "string o null",
                    "tipo_empresa": "string o null"
                }},
                "metadata": {{
                    "calidad_datos": "string (alta/media/baja)",
                    "completitud": "number (0-100)",
                    "confiabilidad": "string (alta/media/baja)",
                    "fecha_procesamiento": "{json.dumps(datetime.now().isoformat())}",
                    "version_cv": "string o null",
                    "idioma_cv": "string"
                }}
            }}
            
            INSTRUCCIONES FINALES CRÍTICAS:
            
            ✅ COMPLETITUD:
            - Extrae TODA la información disponible, no omitas ningún detalle
            - Para cada trabajo, incluye TODAS las responsabilidades mencionadas
            - Lista TODAS las tecnologías, herramientas y frameworks mencionados (no resumas, lista todo)
            - Incluye logros específicos con números, porcentajes, fechas y resultados medibles
            
            🎯 HABILIDADES - MÁXIMA PRIORIDAD:
            - Extrae TODAS las habilidades mencionadas explícita o implícitamente
            - Busca software mencionado: Excel, SAP, Salesforce, Oracle, etc.
            - Identifica herramientas: sistemas, plataformas, aplicaciones
            - Extrae habilidades de las descripciones de trabajo (qué hacía = qué sabe hacer)
            - Categoriza correctamente: técnicas vs blandas, software vs sistemas
            - Genera lista separada por comas en "habilidades_extraidas_experiencia"
            
            📝 DESCRIPCIONES DETALLADAS:
            - Cada experiencia debe tener "descripcion_completa" con 3-5 líneas mínimo
            - Explica qué hacía, cómo lo hacía, con qué herramientas, qué logró
            - Incluye contexto: tamaño de equipo, tipo de proyectos, responsabilidades clave
            
            🔍 ANÁLISIS INTELIGENTE:
            - Si menciona "atención al cliente" → extrae: comunicación, servicio al cliente, resolución de problemas
            - Si menciona "ventas" → extrae: negociación, CRM, prospección, cierre de ventas
            - Si menciona "administración" → extrae: Excel, gestión documental, organización
            - Si menciona "supervisión" → extrae: liderazgo, gestión de equipos, toma de decisiones
            - Si menciona nombres de software/sistemas → agrégalos a las categorías correspondientes
            
            📊 FORMATO Y VALIDACIÓN:
            - Si no encuentras información específica, usa null (no inventes)
            - Para fechas, usa formato YYYY-MM-DD o "YYYY-MM" si solo hay mes/año
            - Para números, usa solo el valor numérico sin símbolos
            - Asegúrate de que el JSON sea válido y completo
            - Todos los arrays deben tener al menos un elemento o estar vacíos []
            
            🎓 EDUCACIÓN Y CERTIFICACIONES:
            - Extrae TODOS los estudios, cursos, certificaciones mencionados
            - Incluye instituciones, fechas, títulos obtenidos
            - Agrega certificaciones profesionales a habilidades también
            
            CV a analizar:
            {cv_text}
            
            IMPORTANTE: Devuelve SOLO el JSON, sin texto adicional antes o después.
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
                    "temperature": 0.2,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 8192
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

