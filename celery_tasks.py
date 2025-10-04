# Celery Tasks para CRM Henmir
# Configuración de tareas asíncronas para notificaciones WhatsApp

import os
from celery import Celery, shared_task
import requests
import mysql.connector
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, Any, Optional
import traceback
from scoring_config import (
    EXPERIENCE_WEIGHTS,
    EDUCATION_WEIGHTS,
    SKILLS_WEIGHTS,
    HISTORY_WEIGHTS,
    AVAILABILITY_WEIGHTS,
    get_candidate_category
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Celery
celery_app = Celery('henmir_crm')

# Configuración del broker (Redis recomendado para producción)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
celery_app.conf.broker_url = REDIS_URL
celery_app.conf.result_backend = REDIS_URL

# Configuraciones adicionales de Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Tegucigalpa',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos máximo por tarea
    task_soft_time_limit=25 * 60,  # 25 minutos soft limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
)

def get_db_connection():
    """Obtiene conexión a la base de datos"""
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'henmir_crm'),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
    except Exception as e:
        logger.error(f"Error conectando a la BD: {e}")
        return None

def clean_phone_number(phone_str):
    """Limpia y estandariza los números de teléfono para Honduras."""
    import re
    if not phone_str:
        return None
    digits = re.sub(r'\D', '', str(phone_str))
    if digits.startswith('504') and len(digits) == 11:
        return digits
    if len(digits) == 8:
        return f"504{digits}"
    return digits if len(digits) >= 8 else None

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_whatsapp_notification_task(self, task_type, related_id, phone_number, message_body, candidate_name=None):
    """
    Tarea asíncrona para enviar notificaciones de WhatsApp.
    
    Args:
        task_type: Tipo de tarea ('postulation', 'interview', 'hired')
        related_id: ID relacionado (postulation_id, interview_id, etc.)
        phone_number: Número de teléfono del destinatario
        message_body: Cuerpo del mensaje a enviar
        candidate_name: Nombre del candidato (opcional)
    
    Returns:
        dict: Resultado de la operación
    """
    try:
        logger.info(f"Iniciando tarea WhatsApp: {task_type} para {candidate_name or 'candidato'}")
        
        # Limpiar número de teléfono
        clean_phone = clean_phone_number(phone_number)
        if not clean_phone:
            raise ValueError(f"Número de teléfono inválido: {phone_number}")
        
        # Preparar datos para bridge.js
        bridge_url = os.getenv('BRIDGE_URL', 'http://localhost:3000')
        task_data = {
            "task_type": task_type,
            "related_id": related_id,
            "chat_id": clean_phone,
            "message_body": message_body,
            "timestamp": datetime.now().isoformat()
        }
        
        # Enviar a bridge.js
        response = requests.post(
            f"{bridge_url}/api/send-task",
            json=task_data,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"Notificación WhatsApp enviada exitosamente: {task_type}")
            
            # Actualizar estado en la base de datos
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    if task_type == 'postulation':
                        cursor.execute(
                            "UPDATE Postulaciones SET whatsapp_notification_status = 'sent' WHERE id_postulacion = %s",
                            (related_id,)
                        )
                    elif task_type == 'interview':
                        cursor.execute(
                            "UPDATE Entrevistas SET notification_status = 'sent' WHERE id_entrevista = %s",
                            (related_id,)
                        )
                    elif task_type == 'hired':
                        cursor.execute(
                            "UPDATE Contratados SET notification_status = 'sent' WHERE id_contratado = %s",
                            (related_id,)
                        )
                    
                    conn.commit()
                    logger.info(f"Estado de notificación actualizado en BD para {task_type}")
                    
                except Exception as db_error:
                    logger.error(f"Error actualizando BD: {db_error}")
                    conn.rollback()
                finally:
                    cursor.close()
                    conn.close()
            
            return {
                'success': True,
                'task_type': task_type,
                'related_id': related_id,
                'phone_number': clean_phone,
                'message': 'Notificación enviada exitosamente'
            }
        else:
            error_msg = f"Error en bridge.js: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
    except Exception as exc:
        logger.error(f"Error en tarea WhatsApp {task_type}: {exc}")
        
        # Actualizar estado de error en BD
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                if task_type == 'postulation':
                    cursor.execute(
                        "UPDATE Postulaciones SET whatsapp_notification_status = 'failed' WHERE id_postulacion = %s",
                        (related_id,)
                    )
                elif task_type == 'interview':
                    cursor.execute(
                        "UPDATE Entrevistas SET notification_status = 'failed' WHERE id_entrevista = %s",
                        (related_id,)
                    )
                elif task_type == 'hired':
                    cursor.execute(
                        "UPDATE Contratados SET notification_status = 'failed' WHERE id_contratado = %s",
                        (related_id,)
                    )
                
                conn.commit()
            except Exception as db_error:
                logger.error(f"Error actualizando estado de fallo en BD: {db_error}")
            finally:
                cursor.close()
                conn.close()
        
        # Re-lanzar excepción para retry automático
        raise self.retry(exc=exc)

@celery_app.task(bind=True)
def get_task_status(self, task_id):
    """
    Obtiene el estado de una tarea de Celery.
    
    Args:
        task_id: ID de la tarea a consultar
    
    Returns:
        dict: Estado de la tarea
    """
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.ready() else None,
            'traceback': result.traceback if result.failed() else None
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado de tarea {task_id}: {e}")
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(e)
        }

# Configuración para auto-discovery de tareas
@celery_app.task(bind=True, name='calculate_candidate_score')
def calculate_candidate_score(self, candidate_id: int) -> Dict[str, Any]:
    """
    Tarea asíncrona para calcular la puntuación de un candidato basada en múltiples factores.
    
    Args:
        candidate_id: ID del candidato/afiliado
        
    Returns:
        dict: Resultado del cálculo con la puntuación y detalles
    """
    try:
        logger.info(f"Iniciando cálculo de puntuación para el candidato {candidate_id}")
        
        # Obtener conexión a la base de datos
        conn = get_db_connection()
        if not conn:
            raise Exception("No se pudo conectar a la base de datos")
            
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 1. Obtener datos básicos del candidato
            cursor.execute("""
                SELECT 
                    a.*,
                    (SELECT COUNT(*) FROM Postulaciones p WHERE p.id_afiliado = a.id_afiliado) as postulaciones_count,
                    (SELECT COUNT(*) FROM Entrevistas e WHERE e.id_afiliado = a.id_afiliado) as entrevistas_count,
                    (SELECT COUNT(*) FROM Contrataciones c WHERE c.id_afiliado = a.id_afiliado) as contrataciones_count,
                    (SELECT GROUP_CONCAT(DISTINCT t.nombre_tag) 
                     FROM Afiliado_Tags at 
                     JOIN Tags t ON at.id_tag = t.id_tag 
                     WHERE at.id_afiliado = a.id_afiliado) as tags
                FROM Afiliados a
                WHERE a.id_afiliado = %s
            """, (candidate_id,))
            
            candidate = cursor.fetchone()
            if not candidate:
                raise ValueError(f"Candidato con ID {candidate_id} no encontrado")
            
            # Inicializar puntuación y detalles
            score = 0
            max_score = 100
            details = {}
            
            # 2. Calcular puntuación basada en experiencia
            experiencia = candidate.get('experiencia', '').lower()
            if 'año' in experiencia or 'años' in experiencia:
                try:
                    # Extraer años de experiencia (ej: "3 años" -> 3)
                    years = int(''.join(filter(str.isdigit, experiencia.split()[0])))
                    exp_score = min(
                        years * EXPERIENCE_WEIGHTS['years_multiplier'], 
                        EXPERIENCE_WEIGHTS['max_points']
                    )
                    score += exp_score
                    details['experiencia'] = {
                        'puntos': exp_score,
                        'detalle': f"{years} años de experiencia"
                    }
                except (ValueError, IndexError) as e:
                    logger.warning(f"No se pudo extraer años de experiencia: {str(e)}")
                    details['experiencia'] = {
                        'puntos': 0,
                        'detalle': 'No se pudo determinar la experiencia',
                        'advertencia': str(e)
                    }
            
            # 3. Puntos por nivel educativo
            educacion = candidate.get('grado_academico', '').lower()
            puntos_educacion = 0
            
            for nivel, puntos in EDUCATION_WEIGHTS.items():
                if nivel in educacion:
                    puntos_educacion = puntos
                    score += puntos
                    details['educacion'] = {
                        'puntos': puntos,
                        'detalle': f"Nivel educativo: {nivel.capitalize()}",
                        'categoria': nivel
                    }
                    break
                    
            if puntos_educacion == 0 and educacion.strip():
                details['educacion'] = {
                    'puntos': 0,
                    'detalle': f"Nivel educativo no reconocido: {educacion}",
                    'advertencia': 'Nivel educativo no reconocido'
                }
            
            # 4. Puntos por habilidades (máximo 20 puntos)
            try:
                habilidades = json.loads(candidate.get('habilidades', '[]'))
                if habilidades and isinstance(habilidades, list):
                    habilidades_score = min(
                        len(habilidades) * SKILLS_WEIGHTS['per_skill'],
                        SKILLS_WEIGHTS['max_points']
                    )
                    score += habilidades_score
                    details['habilidades'] = {
                        'puntos': habilidades_score,
                        'cantidad': len(habilidades),
                        'detalle': f"{len(habilidades)} habilidades registradas"
                    }
            except json.JSONDecodeError:
                logger.warning(f"Formato inválido de habilidades para el candidato {candidate_id}")
                details['habilidades'] = {
                    'puntos': 0,
                    'detalle': 'Formato de habilidades inválido',
                    'advertencia': 'No se pudieron procesar las habilidades'
                }
            
            # 5. Puntos por historial (postulaciones, entrevistas, contrataciones)
            historial_score = 0
            historial_details = []
            
            # Puntos por postulaciones previas
            postulaciones = candidate.get('postulaciones_count', 0)
            if postulaciones > 0:
                post_score = min(
                    postulaciones * HISTORY_WEIGHTS['postulacion']['per_item'],
                    HISTORY_WEIGHTS['postulacion']['max_points']
                )
                historial_score += post_score
                historial_details.append(f"+{post_score} por {postulaciones} postulación(es)")
            
            # Puntos por entrevistas completadas
            entrevistas = candidate.get('entrevistas_count', 0)
            if entrevistas > 0:
                entrevista_score = min(
                    entrevistas * HISTORY_WEIGHTS['entrevista']['per_item'],
                    HISTORY_WEIGHTS['entrevista']['max_points']
                )
                historial_score += entrevista_score
                historial_details.append(f"+{entrevista_score} por {entrevistas} entrevista(s)")
            
            # Puntos por contrataciones previas
            contrataciones = candidate.get('contrataciones_count', 0)
            if contrataciones > 0:
                contrato_score = min(
                    contrataciones * HISTORY_WEIGHTS['contratacion']['per_item'],
                    HISTORY_WEIGHTS['contratacion']['max_points']
                )
                historial_score += contrato_score
                historial_details.append(f"+{contrato_score} por {contrataciones} contratación(es) previa(s)")
            
            # Asegurar que no exceda el máximo para esta categoría
            historial_score = min(historial_score, HISTORY_WEIGHTS['max_total'])
            score += historial_score
            
            if historial_details:
                details['historial'] = {
                    'puntos': historial_score,
                    'detalle': "; ".join(historial_details),
                    'desglose': {
                        'postulaciones': postulaciones,
                        'entrevistas': entrevistas,
                        'contrataciones': contrataciones
                    }
                }
            
            # 6. Puntos por disponibilidad (máximo 10 puntos)
            disponibilidad = candidate.get('disponibilidad', '').lower()
            disp_score = AVAILABILITY_WEIGHTS.get(disponibilidad, AVAILABILITY_WEIGHTS['default'])
            
            if disp_score > 0:
                score += disp_score
                details['disponibilidad'] = {
                    'puntos': disp_score,
                    'disponibilidad': disponibilidad,
                    'detalle': f"Disponibilidad: {disponibilidad.capitalize()}"
                }
            else:
                details['disponibilidad'] = {
                    'puntos': 0,
                    'disponibilidad': 'no especificada',
                    'detalle': 'Disponibilidad no especificada',
                    'advertencia': 'El candidato no ha especificado su disponibilidad'
                }
            
            # 7. Asegurar que el puntaje no exceda el máximo
            score = min(score, max_score)
            
            # 8. Determinar categoría del candidato
            categoria = get_candidate_category(score)
            
            # 9. Actualizar la puntuación en la base de datos
            cursor.execute(
                """
                UPDATE Afiliados 
                SET puntuacion = %s, 
                    categoria_puntuacion = %s,
                    ultima_actualizacion_puntuacion = NOW()
                WHERE id_afiliado = %s
                """,
                (score, categoria, candidate_id)
            )
            
            # 10. Registrar el cálculo en el historial
            cursor.execute(
                """
                INSERT INTO puntuaciones_candidato 
                (id_afiliado, puntuacion, motivo, usuario_id, fecha, detalles, categoria)
                VALUES (%s, %s, %s, %s, NOW(), %s, %s)
                """,
                (candidate_id, score, 'Cálculo automático', 0, json.dumps(details), categoria)
            )
            
            # Agregar resumen al resultado
            details['resumen'] = {
                'puntuacion_total': score,
                'puntuacion_maxima': max_score,
                'categoria': categoria,
                'fecha_calculo': datetime.now().isoformat()
            }
            
            conn.commit()
            
            logger.info(f"Puntuación calculada para el candidato {candidate_id}: {score}/{max_score}")
            
            return {
                'success': True,
                'candidate_id': candidate_id,
                'score': score,
                'max_score': max_score,
                'details': details,
                'message': f'Puntuación calculada exitosamente: {score}/{max_score}'
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al calcular puntuación para el candidato {candidate_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'candidate_id': candidate_id,
                'error': str(e),
                'message': 'Error al calcular la puntuación'
            }
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error en calculate_candidate_score: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'candidate_id': candidate_id,
            'error': str(e),
            'message': 'Error al procesar la solicitud'
        }


def get_db_connection():
    """Obtiene una conexión a la base de datos"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT', '3306')),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        return conn
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {str(e)}")
        return None


if __name__ == '__main__':
    celery_app.start()
