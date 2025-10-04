#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import PyPDF2
import docx
from PIL import Image
import pytesseract
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CVProcessor:
    """Procesador principal de CVs con múltiples APIs de Gemini"""
    
    def __init__(self):
        """Inicializar el procesador con múltiples API keys de Gemini"""
        self.gemini_api_keys = [
            os.getenv('GEMINI_API_KEY_1'),
            os.getenv('GEMINI_API_KEY_2'), 
            os.getenv('GEMINI_API_KEY_3'),
            os.getenv('GEMINI_API_KEY_4'),
            os.getenv('GEMINI_API_KEY_5')
        ]
        
        # Filtrar API keys válidas
        self.valid_api_keys = [key for key in self.gemini_api_keys if key]
        
        if not self.valid_api_keys:
            raise ValueError("No se encontraron API keys válidas de Gemini")
        
        logger.info(f"Configuradas {len(self.valid_api_keys)} API keys de Gemini")
        
        # Configurar modelos
        self.models = []
        for i, api_key in enumerate(self.valid_api_keys):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                self.models.append({
                    'model': model,
                    'api_key': api_key,
                    'index': i,
                    'available': True,
                    'last_used': None
                })
                logger.info(f"Modelo Gemini {i+1} configurado correctamente")
            except Exception as e:
                logger.error(f"Error configurando modelo Gemini {i+1}: {e}")
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """Extraer texto de diferentes tipos de archivos"""
        try:
            if file_type.lower() == 'pdf':
                return self._extract_from_pdf(file_path)
            elif file_type.lower() in ['docx', 'doc']:
                return self._extract_from_docx(file_path)
            elif file_type.lower() in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                return self._extract_from_image(file_path)
            else:
                raise ValueError(f"Tipo de archivo no soportado: {file_type}")
        except Exception as e:
            logger.error(f"Error extrayendo texto de {file_path}: {e}")
            raise
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extraer texto de PDF"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error extrayendo PDF {file_path}: {e}")
            raise
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extraer texto de DOCX"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extrayendo DOCX {file_path}: {e}")
            raise
    
    def _extract_from_image(self, file_path: str) -> str:
        """Extraer texto de imagen usando OCR"""
        try:
            # Verificar si Tesseract está disponible
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                logger.warning(f"Tesseract no está instalado. Saltando OCR para {file_path}")
                return "Imagen procesada - OCR no disponible (Tesseract no instalado)"
            
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='spa+eng')
            return text.strip() if text.strip() else "No se pudo extraer texto de la imagen"
        except Exception as e:
            logger.error(f"Error extrayendo imagen {file_path}: {e}")
            return f"Error procesando imagen: {str(e)}"
    
    def normalize_text(self, text: str) -> str:
        """Normalizar texto extraído"""
        # Limpiar caracteres especiales
        text = re.sub(r'\s+', ' ', text)  # Múltiples espacios a uno
        text = re.sub(r'\n+', '\n', text)  # Múltiples saltos de línea a uno
        text = text.strip()
        
        # Limpiar caracteres de control
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return text
    
    def get_available_model(self) -> Optional[Dict]:
        """Obtener un modelo disponible de Gemini"""
        available_models = [model for model in self.models if model['available']]
        
        if not available_models:
            logger.warning("No hay modelos disponibles")
            return None
        
        # Seleccionar el modelo menos usado recientemente
        available_models.sort(key=lambda x: x['last_used'] or datetime.min)
        return available_models[0]
    
    def mark_model_busy(self, model_index: int):
        """Marcar modelo como ocupado"""
        for model in self.models:
            if model['index'] == model_index:
                model['available'] = False
                model['last_used'] = datetime.now()
                break
    
    def mark_model_available(self, model_index: int):
        """Marcar modelo como disponible"""
        for model in self.models:
            if model['index'] == model_index:
                model['available'] = True
                break
    
    async def extract_candidate_data(self, cv_text: str, cv_id: str) -> Dict[str, Any]:
        """Extraer datos del candidato usando Gemini"""
        model_info = self.get_available_model()
        
        if not model_info:
            logger.warning("No hay modelos de Gemini disponibles, usando modo fallback")
            return self._extract_basic_data_fallback(cv_text, cv_id)
        
        model = model_info['model']
        model_index = model_info['index']
        
        try:
            self.mark_model_busy(model_index)
            
            # Prompt optimizado para extracción de datos con manejo de datos faltantes
            prompt = f"""
Analiza el siguiente CV y extrae la información en formato JSON estricto.
Solo devuelve el JSON, sin texto adicional.

Formato requerido:
{{
    "nombre_completo": "string o null",
    "email": "string o null",
    "telefono": "string o null",
    "ciudad": "string o null", 
    "cargo_solicitado": "string o null",
    "experiencia": "string o null",
    "habilidades": "string o null",
    "grado_academico": "string o null",
    "fecha_nacimiento": "YYYY-MM-DD o null",
    "nacionalidad": "string o null",
    "linkedin": "string o null",
    "portfolio": "string o null",
    "comentarios": "string o null"
}}

CV a analizar:
{cv_text}

INSTRUCCIONES IMPORTANTES:
- EXTRAE TODA LA INFORMACIÓN DISPONIBLE del CV de manera inteligente
- Busca nombres completos en cualquier parte del documento
- Busca emails en formato "texto@dominio.com" 
- Busca teléfonos, números de contacto, celulares
- Busca direcciones, ciudades, ubicaciones
- Busca experiencia laboral, trabajos anteriores
- Para HABILIDADES: Extrae habilidades de:
  * Experiencia laboral (qué hacía en cada trabajo)
  * Educación (carreras, cursos, certificaciones)
  * Proyectos mencionados
  * Software, herramientas, tecnologías mencionadas
  * Idiomas, competencias específicas
- Busca educación, títulos, grados académicos
- Si NO encuentras información específica después de buscar exhaustivamente, usa null
- NO inventes información que no esté en el CV
- El email debe ser válido si existe
- El teléfono debe incluir código de país si está disponible
- La experiencia debe ser un resumen de 2-3 líneas si está disponible
- Las habilidades deben ser una lista separada por comas si están disponibles
- Prioriza la COMPLETITUD sobre la exactitud - extrae todo lo que encuentres
- Si no hay email, es normal, usa null
"""

            # Generar respuesta con Gemini
            response = await asyncio.to_thread(
                model.generate_content, prompt
            )
            
            # Extraer JSON de la respuesta
            response_text = response.text.strip()
            
            # Limpiar respuesta para extraer solo JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text
            
            # Parsear JSON
            candidate_data = json.loads(json_str)
            
            # Importar completador de datos
            from cv_data_completer import create_data_completer
            data_completer = create_data_completer()
            
            # Completar datos faltantes usando el texto original
            candidate_data = data_completer.complete_missing_data(candidate_data, cv_text)
            
            # Validar datos completados
            is_valid, errors = data_completer.validate_completed_data(candidate_data)
            
            if not is_valid:
                logger.warning(f"CV {cv_id} tiene datos inválidos: {errors}")
                # Continuar con los datos disponibles
            
            # Agregar metadatos
            candidate_data['cv_id'] = cv_id
            candidate_data['processed_at'] = datetime.now().isoformat()
            candidate_data['model_used'] = f"gemini_{model_index + 1}"
            candidate_data['validation_errors'] = errors
            candidate_data['is_valid'] = is_valid
            
            logger.info(f"CV {cv_id} procesado exitosamente con modelo {model_index + 1}")
            return candidate_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON para CV {cv_id}: {e}")
            raise ValueError(f"Error parseando respuesta de IA: {e}")
        except Exception as e:
            logger.error(f"Error procesando CV {cv_id} con modelo {model_index + 1}: {e}")
            raise
        finally:
            self.mark_model_available(model_index)
    
    def process_cv_batch(self, cv_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Procesar lote de CVs usando múltiples modelos en paralelo"""
        results = []
        
        # Procesar en paralelo usando ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(self.valid_api_keys)) as executor:
            # Crear tareas asíncronas
            futures = []
            for cv_data in cv_batch:
                future = executor.submit(
                    self._process_single_cv_sync,
                    cv_data['text'],
                    cv_data['cv_id'],
                    cv_data['file_name']
                )
                futures.append(future)
            
            # Recopilar resultados
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error procesando CV en lote: {e}")
                    results.append({
                        'cv_id': 'unknown',
                        'error': str(e),
                        'status': 'failed'
                    })
        
        return results
    
    def _process_single_cv_sync(self, cv_text: str, cv_id: str, file_name: str) -> Dict[str, Any]:
        """Procesar un CV individual de forma síncrona"""
        try:
            # Ejecutar en loop de eventos para manejar async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.extract_candidate_data(cv_text, cv_id)
            )
            
            result['file_name'] = file_name
            result['status'] = 'success'
            
            return result
            
        except Exception as e:
            logger.error(f"Error procesando CV {cv_id}: {e}")
            return {
                'cv_id': cv_id,
                'file_name': file_name,
                'error': str(e),
                'status': 'failed'
            }
        finally:
            loop.close()

# Función de utilidad para crear instancia del procesador
def create_cv_processor() -> CVProcessor:
    """Crear instancia del procesador de CVs"""
    return CVProcessor()

if __name__ == "__main__":
    # Prueba del procesador
    processor = create_cv_processor()
    print(f"Procesador configurado con {len(processor.valid_api_keys)} modelos de Gemini")
