"""
Procesamiento optimizado en lotes para carga masiva de CVs
"""

import concurrent.futures
import time
from typing import List, Dict, Any

def process_batch_optimized(batch_files: List[Dict], tenant_id: int, user_id: int) -> Dict[str, Any]:
    """
    Procesar lote de archivos con optimizaciones paralelas
    
    Args:
        batch_files: Lista de archivos del lote
        tenant_id: ID del tenant
        user_id: ID del usuario
        
    Returns:
        Dict con resultados y errores del lote
    """
    batch_results = []
    errors = []
    
    # PASO 1: Subir todos los archivos del lote a OCI (paralelo)
    upload_tasks = []
    
    for file_data in batch_files:
        try:
            cv_identifier = oci_storage_service.generate_cv_identifier(
                tenant_id=tenant_id,
                candidate_id=None
            )
            
            upload_result = oci_storage_service.upload_cv(
                file_content=file_data['content'],
                tenant_id=tenant_id,
                cv_identifier=cv_identifier,
                original_filename=file_data['filename'],
                candidate_id=None
            )
            
            if upload_result['success']:
                par_result = oci_storage_service.create_par(
                    object_key=upload_result['object_key'],
                    cv_identifier=cv_identifier
                )
                
                if par_result['success']:
                    upload_tasks.append({
                        'file_data': file_data,
                        'cv_identifier': cv_identifier,
                        'upload_result': upload_result,
                        'par_result': par_result
                    })
                else:
                    errors.append({
                        'filename': file_data['filename'],
                        'error': f"Error creando PAR: {par_result['error']}"
                    })
            else:
                errors.append({
                    'filename': file_data['filename'],
                    'error': f"Error subiendo a OCI: {upload_result['error']}"
                })
                
        except Exception as e:
            errors.append({
                'filename': file_data['filename'],
                'error': f"Error preparando archivo: {str(e)}"
            })
    
    # PASO 2: Procesar textos con Gemini en paralelo
    if upload_tasks:
        cv_texts = []
        for task in upload_tasks:
            try:
                cv_text = cv_processing_service.extract_text_from_file(
                    file_content=task['file_data']['content'],
                    filename=task['file_data']['filename']
                )
                cv_texts.append(cv_text)
            except Exception as e:
                errors.append({
                    'filename': task['file_data']['filename'],
                    'error': f"Error extrayendo texto: {str(e)}"
                })
                cv_texts.append("")  # Placeholder para mantener índices
        
        # Procesar lote completo con Gemini en paralelo
        gemini_results = cv_processing_service.process_cv_batch(cv_texts, tenant_id)
        
        # PASO 3: Crear candidatos y guardar en BD
        for task, gemini_result in zip(upload_tasks, gemini_results):
            if gemini_result and gemini_result.get('success'):
                try:
                    validation_result = cv_processing_service.validate_cv_data(
                        gemini_result['data']
                    )
                    
                    if validation_result['success']:
                        processed_data = validation_result['validated_data']
                        
                        # Crear candidato
                        candidate_id = create_candidate_from_cv_data(
                            processed_data, tenant_id, user_id
                        )
                        
                        # Guardar CV en BD
                        save_cv_to_database(
                            tenant_id=tenant_id,
                            candidate_id=candidate_id,
                            cv_identifier=task['cv_identifier'],
                            original_filename=task['file_data']['filename'],
                            object_key=task['upload_result']['object_key'],
                            file_url=task['par_result']['access_uri'],
                            par_id=task['par_result']['par_id'],
                            mime_type=task['upload_result']['mime_type'],
                            file_size=task['upload_result']['size'],
                            processed_data=processed_data
                        )
                        
                        batch_results.append({
                            'filename': task['file_data']['filename'],
                            'success': True,
                            'cv_identifier': task['cv_identifier'],
                            'candidate_id': candidate_id,
                            'processed_data': processed_data
                        })
                    else:
                        errors.append({
                            'filename': task['file_data']['filename'],
                            'error': f"Error validando datos: {validation_result['error']}"
                        })
                except Exception as e:
                    errors.append({
                        'filename': task['file_data']['filename'],
                        'error': f"Error creando candidato: {str(e)}"
                    })
            else:
                errors.append({
                    'filename': task['file_data']['filename'],
                    'error': f"Error procesando con IA: {gemini_result.get('error', 'Error desconocido') if gemini_result else 'No se procesó'}"
                })
    
    return {
        'results': batch_results,
        'errors': errors
    }
