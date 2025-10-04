#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import mysql.connector
from dotenv import load_dotenv

from cv_processor import CVProcessor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CVBatchManager:
    """Gestor de procesamiento por lotes de CVs"""
    
    def __init__(self):
        """Inicializar el gestor de lotes"""
        self.cv_processor = CVProcessor()
        self.batch_size = 50  # Tamaño de lote por defecto
        self.max_workers = 5  # Máximo de workers paralelos
        
        # Cargar configuración de base de datos
        load_dotenv()
    
    def get_db_connection(self):
        """Obtener conexión a la base de datos"""
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'crm_henmir')
        )
    
    def create_job(self, files: List[Dict[str, Any]], tenant_id: int, user_id: int) -> str:
        """Crear un nuevo trabajo de procesamiento"""
        job_id = str(uuid.uuid4())
        
        # Guardar información del trabajo
        job_data = {
            'job_id': job_id,
            'tenant_id': tenant_id,
            'user_id': user_id,
            'total_files': len(files),
            'files': files,  # Agregar los archivos al job_data
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'processed_files': 0,
            'successful': 0,
            'errors': 0,
            'duplicates': 0,
            'batches': [],
            'results': []
        }
        
        # Guardar en archivo temporal (en producción usar Redis o DB)
        job_file = f"temp_jobs/{job_id}.json"
        os.makedirs("temp_jobs", exist_ok=True)
        
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Trabajo {job_id} creado para {len(files)} archivos")
        return job_id
    
    def process_job(self, job_id: str) -> Dict[str, Any]:
        """Procesar un trabajo completo"""
        job_file = f"temp_jobs/{job_id}.json"
        
        if not os.path.exists(job_file):
            raise FileNotFoundError(f"Trabajo {job_id} no encontrado")
        
        # Cargar datos del trabajo
        with open(job_file, 'r', encoding='utf-8') as f:
            job_data = json.load(f)
        
        try:
            # Actualizar estado
            job_data['status'] = 'processing'
            job_data['started_at'] = datetime.now().isoformat()
            self._save_job_data(job_id, job_data)
            
            # Procesar archivos
            results = self._process_files(job_data)
            
            # Actualizar resultados
            job_data['status'] = 'completed'
            job_data['completed_at'] = datetime.now().isoformat()
            job_data['results'] = results
            
            self._save_job_data(job_id, job_data)
            
            logger.info(f"Trabajo {job_id} completado exitosamente")
            return job_data
            
        except Exception as e:
            logger.error(f"Error procesando trabajo {job_id}: {e}")
            job_data['status'] = 'failed'
            job_data['error'] = str(e)
            job_data['failed_at'] = datetime.now().isoformat()
            self._save_job_data(job_id, job_data)
            raise
    
    def _process_files(self, job_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Procesar todos los archivos del trabajo"""
        # Simular archivos (en implementación real vendrían del request)
        files = job_data.get('files', [])
        
        if not files:
            raise ValueError("No hay archivos para procesar")
        
        # Dividir en lotes
        batches = self._create_batches(files, self.batch_size)
        job_data['batches'] = batches
        
        all_results = []
        
        # Procesar cada lote
        for batch_index, batch in enumerate(batches):
            logger.info(f"Procesando lote {batch_index + 1}/{len(batches)}")
            
            # Verificar si el trabajo fue cancelado
            if job_data.get('status') == 'cancelled':
                logger.info(f"Trabajo {job_id} cancelado")
                break
            
            try:
                # Convertir archivos a texto primero
                text_batch = []
                for file_data in batch:
                    try:
                        logger.info(f"Convirtiendo archivo: {file_data['original_name']}")
                        text = self.cv_processor.extract_text_from_file(
                            file_data['file_path'], 
                            file_data['file_type']
                        )
                        
                        text_batch.append({
                            'cv_id': file_data['file_path'],
                            'text': text,
                            'file_name': file_data['original_name'],
                            'file_type': file_data['file_type']
                        })
                        logger.info(f"Texto extraído: {len(text)} caracteres")
                    except Exception as e:
                        logger.error(f"Error convirtiendo archivo {file_data['original_name']}: {e}")
                        text_batch.append({
                            'cv_id': file_data['file_path'],
                            'text': '',
                            'file_name': file_data['original_name'],
                            'file_type': file_data['file_type'],
                            'error': str(e)
                        })
                
                # Procesar lote de textos
                try:
                    logger.info(f"Procesando {len(text_batch)} archivos con IA...")
                    batch_results = self.cv_processor.process_cv_batch(text_batch)
                    logger.info(f"IA procesó {len(batch_results)} resultados")
                except Exception as e:
                    logger.error(f"Error procesando lote {batch_index + 1}: {e}")
                    batch_results = [{
                        'cv_id': 'error',
                        'error': str(e),
                        'status': 'failed'
                    }]
                
                # Guardar candidatos en base de datos
                logger.info(f"Guardando {len(batch_results)} candidatos en base de datos...")
                saved_results = self._save_candidates_to_db(
                    batch_results, 
                    job_data['tenant_id'], 
                    job_data['user_id']
                )
                logger.info(f"Guardados {len(saved_results)} candidatos exitosamente")
                
                all_results.extend(saved_results)
                
                # Actualizar progreso
                job_data['processed_files'] += len(batch)
                job_data['successful'] += len([r for r in saved_results if r.get('status') == 'success'])
                job_data['errors'] += len([r for r in saved_results if r.get('status') == 'failed'])
                
                self._save_job_data(job_data['job_id'], job_data)
                
            except Exception as e:
                logger.error(f"Error procesando lote {batch_index + 1}: {e}")
                # Continuar con el siguiente lote
                continue
        
        return all_results
    
    def _create_batches(self, files: List[Dict[str, Any]], batch_size: int) -> List[List[Dict[str, Any]]]:
        """Crear lotes de archivos"""
        batches = []
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            batches.append(batch)
        return batches
    
    def _save_candidates_to_db(self, candidates: List[Dict[str, Any]], tenant_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Guardar candidatos en la base de datos"""
        logger.info(f"Iniciando guardado de {len(candidates)} candidatos para tenant {tenant_id}")
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        saved_results = []
        
        try:
            # Importar detector de duplicados
            from cv_duplicate_detector import create_duplicate_detector
            duplicate_detector = create_duplicate_detector()
            
            for i, candidate in enumerate(candidates):
                logger.info(f"Procesando candidato {i+1}/{len(candidates)}: {candidate.get('nombre_completo', 'Sin nombre')}")
                
                if candidate.get('status') == 'failed':
                    logger.warning(f"Candidato {i+1} marcado como fallido, saltando...")
                    saved_results.append(candidate)
                    continue
                
                try:
                    # Validar datos antes de procesar
                    if not candidate.get('nombre_completo'):
                        logger.warning(f"Candidato {i+1} inválido: falta nombre completo")
                        saved_results.append({
                            'cv_id': candidate.get('cv_id', 'unknown'),
                            'error': 'Datos insuficientes: falta nombre completo',
                            'status': 'failed',
                            'candidate': candidate
                        })
                        continue
                    
                    # Si no hay email, generar uno temporal basado en el nombre
                    if not candidate.get('email'):
                        logger.info(f"Candidato {i+1} sin email, generando temporal")
                        # Generar email temporal: nombre.apellido@temp.com
                        nombre_parts = candidate.get('nombre_completo', '').lower().split()
                        if len(nombre_parts) >= 2:
                            email_temp = f"{nombre_parts[0]}.{nombre_parts[1]}@temp.com"
                        else:
                            email_temp = f"{nombre_parts[0]}@temp.com"
                        candidate['email'] = email_temp
                        candidate['email_temporal'] = True
                    
                    # Buscar duplicados usando múltiples criterios
                    duplicates = duplicate_detector.find_duplicates_comprehensive(candidate, tenant_id)
                    
                    if duplicates:
                        # Hay duplicados, usar el más confiable
                        best_duplicate = None
                        best_confidence = 0.0
                        
                        for duplicate in duplicates:
                            confidence = duplicate_detector.calculate_duplicate_confidence(candidate, duplicate)
                            if confidence > best_confidence:
                                best_confidence = confidence
                                best_duplicate = duplicate
                        
                        if best_confidence >= 0.5:  # Umbral de confianza
                            # Actualizar candidato existente
                            logger.info(f"Actualizando candidato existente ID {best_duplicate['id_afiliado']} (confianza: {best_confidence:.2f})")
                            updated = self._update_candidate(best_duplicate['id_afiliado'], candidate, cursor)
                            saved_results.append({
                                'action': 'updated',
                                'candidate_id': best_duplicate['id_afiliado'],
                                'candidate': updated,
                                'status': 'success',
                                'duplicate_confidence': best_confidence,
                                'duplicate_type': duplicate_detector.classify_duplicate(candidate, best_duplicate)
                            })
                        else:
                            # Confianza baja, crear nuevo candidato
                            logger.info(f"Creando nuevo candidato (confianza duplicado: {best_confidence:.2f})")
                            new_id = self._create_candidate(candidate, tenant_id, user_id, cursor)
                            saved_results.append({
                                'action': 'created',
                                'candidate_id': new_id,
                                'candidate': candidate,
                                'status': 'success',
                                'duplicate_confidence': best_confidence,
                                'duplicate_type': 'low_confidence'
                            })
                    else:
                        # No hay duplicados, crear nuevo candidato
                        logger.info("No hay duplicados, creando nuevo candidato")
                        new_id = self._create_candidate(candidate, tenant_id, user_id, cursor)
                        saved_results.append({
                            'action': 'created',
                            'candidate_id': new_id,
                            'candidate': candidate,
                            'status': 'success',
                            'duplicate_confidence': 0.0,
                            'duplicate_type': 'none'
                        })
                
                except ValueError as e:
                    # Error de validación - datos insuficientes
                    logger.warning(f"Candidato {i+1} inválido: {e}")
                    saved_results.append({
                        'cv_id': candidate.get('cv_id', 'unknown'),
                        'error': str(e),
                        'status': 'failed',
                        'candidate': candidate
                    })
                except Exception as e:
                    # Error de base de datos u otro
                    logger.error(f"Error guardando candidato {candidate.get('cv_id', 'unknown')}: {e}")
                    saved_results.append({
                        'cv_id': candidate.get('cv_id', 'unknown'),
                        'error': str(e),
                        'status': 'failed',
                        'candidate': candidate
                    })
            
            conn.commit()
            logger.info(f"Transacción completada exitosamente. {len(saved_results)} candidatos procesados")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción de base de datos: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
        
        logger.info(f"Guardado completado: {len(saved_results)} resultados")
        return saved_results
    
    def _check_duplicate(self, email: str, tenant_id: int, cursor) -> Optional[Dict[str, Any]]:
        """Verificar si existe un candidato con el mismo email en el tenant"""
        cursor.execute("""
            SELECT id_afiliado, nombre_completo, email, fecha_registro
            FROM Afiliados 
            WHERE email = %s
        """, (email,))
        
        result = cursor.fetchone()
        if result:
            return {
                'id_afiliado': result[0],
                'nombre_completo': result[1],
                'email': result[2],
                'fecha_registro': result[3]
            }
        return None
    
    def _create_candidate(self, candidate_data: Dict[str, Any], tenant_id: int, user_id: int, cursor) -> int:
        """Crear nuevo candidato en la base de datos"""
        
        # Validar campos obligatorios
        nombre_completo = candidate_data.get('nombre_completo')
        email = candidate_data.get('email')
        
        if not nombre_completo or nombre_completo.strip() == '':
            raise ValueError("nombre_completo es obligatorio y no puede estar vacío")
        
        if not email or email.strip() == '':
            raise ValueError("email es obligatorio y no puede estar vacío")
        
        # Limpiar y validar datos
        nombre_completo = nombre_completo.strip()
        email = email.strip()
        
        # Validar formato de email básico
        if '@' not in email or '.' not in email:
            raise ValueError(f"email inválido: {email}")
        
        # Convertir habilidades a JSON válido
        habilidades_text = candidate_data.get('habilidades')
        habilidades_json = None
        if habilidades_text:
            # Si es texto, convertirlo a JSON array
            if isinstance(habilidades_text, str):
                # Dividir por comas y crear array JSON
                habilidades_list = [h.strip() for h in habilidades_text.split(',') if h.strip()]
                habilidades_json = json.dumps(habilidades_list, ensure_ascii=False)
            else:
                habilidades_json = json.dumps(habilidades_text, ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO Afiliados (
                tenant_id, nombre_completo, email, telefono, ciudad, cargo_solicitado,
                experiencia, habilidades, grado_academico, fecha_nacimiento,
                nacionalidad, linkedin, portfolio, skills, comentarios,
                fecha_registro, fuente_reclutamiento
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), 'CV Upload'
            )
        """, (
            tenant_id,
            nombre_completo,
            email,
            candidate_data.get('telefono') or None,
            candidate_data.get('ciudad') or None,
            candidate_data.get('cargo_solicitado') or None,
            candidate_data.get('experiencia') or None,
            habilidades_json,
            candidate_data.get('grado_academico') or None,
            candidate_data.get('fecha_nacimiento') or None,
            candidate_data.get('nacionalidad') or None,
            candidate_data.get('linkedin') or None,
            candidate_data.get('portfolio') or None,
            candidate_data.get('skills') or None,
            candidate_data.get('comentarios') or None
        ))
        
        return cursor.lastrowid
    
    def _update_candidate(self, candidate_id: int, candidate_data: Dict[str, Any], cursor) -> Dict[str, Any]:
        """Actualizar candidato existente"""
        cursor.execute("""
            UPDATE Afiliados SET
                nombre_completo = %s,
                telefono = %s,
                ciudad = %s,
                cargo_solicitado = %s,
                experiencia = %s,
                habilidades = %s,
                grado_academico = %s,
                fecha_nacimiento = %s,
                nacionalidad = %s,
                linkedin = %s,
                portfolio = %s,
                skills = %s,
                comentarios = %s,
                updated_at = NOW()
            WHERE id_afiliado = %s
        """, (
            candidate_data.get('nombre_completo'),
            candidate_data.get('telefono'),
            candidate_data.get('ciudad'),
            candidate_data.get('cargo_solicitado'),
            candidate_data.get('experiencia'),
            candidate_data.get('habilidades'),
            candidate_data.get('grado_academico'),
            candidate_data.get('fecha_nacimiento'),
            candidate_data.get('nacionalidad'),
            candidate_data.get('linkedin'),
            candidate_data.get('portfolio'),
            candidate_data.get('skills'),
            candidate_data.get('comentarios'),
            candidate_id
        ))
        
        return candidate_data
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Obtener estado de un trabajo"""
        job_file = f"temp_jobs/{job_id}.json"
        
        if not os.path.exists(job_file):
            raise FileNotFoundError(f"Trabajo {job_id} no encontrado")
        
        with open(job_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_job_data(self, job_id: str, job_data: Dict[str, Any]):
        """Guardar datos del trabajo"""
        job_file = f"temp_jobs/{job_id}.json"
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, indent=2, ensure_ascii=False)
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancelar un trabajo"""
        job_file = f"temp_jobs/{job_id}.json"
        
        if not os.path.exists(job_file):
            return {'error': 'Trabajo no encontrado'}
        
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                job_data = json.load(f)
            
            job_data['status'] = 'cancelled'
            job_data['cancelled_at'] = datetime.now().isoformat()
            
            with open(job_file, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Trabajo {job_id} cancelado")
            return {'success': True, 'message': 'Trabajo cancelado'}
        except Exception as e:
            logger.error(f"Error cancelando trabajo {job_id}: {e}")
            return {'error': str(e)}

# Función de utilidad
def create_batch_manager() -> CVBatchManager:
    """Crear instancia del gestor de lotes"""
    return CVBatchManager()

if __name__ == "__main__":
    # Prueba del gestor
    manager = create_batch_manager()
    print("Gestor de lotes configurado correctamente")
