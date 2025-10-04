"""
WhatsApp Business API Manager
============================
Maneja todas las interacciones con la API oficial de WhatsApp Business.
Incluye envío de mensajes, templates, multimedia y gestión de estados.
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import mysql.connector
from mysql.connector import Error

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppBusinessAPIManager:
    """Gestor de la API oficial de WhatsApp Business"""
    
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.db_config = {
            'host': 'localhost',
            'database': 'reclutamiento_db',
            'user': 'root',
            'password': 'admin123'
        }
    
    def get_tenant_config(self, tenant_id: int) -> Optional[Dict]:
        """Obtiene la configuración de WhatsApp para un tenant específico"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT wa_api_type, wa_access_token, wa_phone_number_id, 
                       wa_webhook_url, wa_business_account_id
                FROM WhatsApp_Config 
                WHERE tenant_id = %s AND wa_active = TRUE
            """
            cursor.execute(query, (tenant_id,))
            config = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if config and config['wa_api_type'] == 'business_api':
                return config
            return None
            
        except Error as e:
            logger.error(f"Error obteniendo configuración tenant {tenant_id}: {e}")
            return None
    
    def send_text_message(self, tenant_id: int, to: str, message: str, 
                         message_id: Optional[str] = None) -> Dict:
        """
        Envía un mensaje de texto a través de WhatsApp Business API
        
        Args:
            tenant_id: ID del tenant
            to: Número de teléfono destino (formato internacional sin +)
            message: Contenido del mensaje
            message_id: ID del mensaje (para respuestas)
        
        Returns:
            Dict con status, message_id y detalles de la respuesta
        """
        try:
            config = self.get_tenant_config(tenant_id)
            if not config:
                return {
                    "status": "error",
                    "error": "No hay configuración de WhatsApp Business API activa para este tenant"
                }
            
            # Preparar URL y headers
            url = f"{self.base_url}/{config['wa_phone_number_id']}/messages"
            headers = {
                "Authorization": f"Bearer {config['wa_access_token']}",
                "Content-Type": "application/json"
            }
            
            # Preparar payload
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            # Si es respuesta a un mensaje específico
            if message_id:
                payload["context"] = {"message_id": message_id}
            
            # Enviar mensaje
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                whatsapp_message_id = response_data.get('messages', [{}])[0].get('id')
                
                # Guardar mensaje en BD
                self._save_outgoing_message(
                    tenant_id=tenant_id,
                    to=to,
                    message=message,
                    whatsapp_message_id=whatsapp_message_id,
                    message_type='text',
                    status='sent'
                )
                
                return {
                    "status": "success",
                    "message_id": whatsapp_message_id,
                    "response": response_data
                }
            else:
                error_msg = f"Error API WhatsApp: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "error": error_msg
                }
                
        except Exception as e:
            error_msg = f"Error enviando mensaje: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def send_template_message(self, tenant_id: int, to: str, template_name: str, 
                            template_params: List[str] = None) -> Dict:
        """
        Envía un mensaje template a través de WhatsApp Business API
        
        Args:
            tenant_id: ID del tenant
            to: Número de teléfono destino
            template_name: Nombre del template aprobado
            template_params: Parámetros para el template
        
        Returns:
            Dict con status y detalles de la respuesta
        """
        try:
            config = self.get_tenant_config(tenant_id)
            if not config:
                return {
                    "status": "error",
                    "error": "No hay configuración de WhatsApp Business API activa"
                }
            
            url = f"{self.base_url}/{config['wa_phone_number_id']}/messages"
            headers = {
                "Authorization": f"Bearer {config['wa_access_token']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "es"}
                }
            }
            
            # Agregar parámetros si existen
            if template_params:
                payload["template"]["components"] = [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": param} for param in template_params]
                }]
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                whatsapp_message_id = response_data.get('messages', [{}])[0].get('id')
                
                # Guardar mensaje template en BD
                self._save_outgoing_message(
                    tenant_id=tenant_id,
                    to=to,
                    message=f"Template: {template_name}",
                    whatsapp_message_id=whatsapp_message_id,
                    message_type='template',
                    status='sent',
                    template_name=template_name
                )
                
                return {
                    "status": "success",
                    "message_id": whatsapp_message_id,
                    "response": response_data
                }
            else:
                error_msg = f"Error enviando template: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "error": error_msg
                }
                
        except Exception as e:
            error_msg = f"Error enviando template: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def send_media_message(self, tenant_id: int, to: str, media_type: str, 
                          media_url: str, caption: str = None) -> Dict:
        """
        Envía un mensaje multimedia (imagen, documento, audio, video)
        
        Args:
            tenant_id: ID del tenant
            to: Número de teléfono destino
            media_type: Tipo de media (image, document, audio, video)
            media_url: URL del archivo multimedia
            caption: Texto descriptivo (opcional)
        
        Returns:
            Dict con status y detalles de la respuesta
        """
        try:
            config = self.get_tenant_config(tenant_id)
            if not config:
                return {
                    "status": "error",
                    "error": "No hay configuración de WhatsApp Business API activa"
                }
            
            url = f"{self.base_url}/{config['wa_phone_number_id']}/messages"
            headers = {
                "Authorization": f"Bearer {config['wa_access_token']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": media_type,
                media_type: {
                    "link": media_url
                }
            }
            
            # Agregar caption si existe
            if caption and media_type in ['image', 'document', 'video']:
                payload[media_type]["caption"] = caption
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                whatsapp_message_id = response_data.get('messages', [{}])[0].get('id')
                
                # Guardar mensaje multimedia en BD
                self._save_outgoing_message(
                    tenant_id=tenant_id,
                    to=to,
                    message=f"{media_type}: {media_url}",
                    whatsapp_message_id=whatsapp_message_id,
                    message_type=media_type,
                    status='sent',
                    media_url=media_url,
                    caption=caption
                )
                
                return {
                    "status": "success",
                    "message_id": whatsapp_message_id,
                    "response": response_data
                }
            else:
                error_msg = f"Error enviando media: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "error": error_msg
                }
                
        except Exception as e:
            error_msg = f"Error enviando media: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def get_message_status(self, tenant_id: int, message_id: str) -> Dict:
        """
        Obtiene el estado de un mensaje enviado
        
        Args:
            tenant_id: ID del tenant
            message_id: ID del mensaje de WhatsApp
        
        Returns:
            Dict con el estado del mensaje
        """
        try:
            config = self.get_tenant_config(tenant_id)
            if not config:
                return {
                    "status": "error",
                    "error": "No hay configuración de WhatsApp Business API activa"
                }
            
            # Buscar en BD el mensaje
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT wa_status, wa_timestamp, wa_error_message
                FROM WhatsApp_Messages 
                WHERE wa_message_id = %s AND tenant_id = %s
            """
            cursor.execute(query, (message_id, tenant_id))
            message_data = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if message_data:
                return {
                    "status": "success",
                    "message_status": message_data['wa_status'],
                    "timestamp": message_data['wa_timestamp'],
                    "error": message_data['wa_error_message']
                }
            else:
                return {
                    "status": "error",
                    "error": "Mensaje no encontrado"
                }
                
        except Exception as e:
            error_msg = f"Error obteniendo estado: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def _save_outgoing_message(self, tenant_id: int, to: str, message: str, 
                              whatsapp_message_id: str, message_type: str, 
                              status: str, template_name: str = None, 
                              media_url: str = None, caption: str = None):
        """Guarda un mensaje saliente en la base de datos"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Buscar o crear conversación
            conversation_id = self._get_or_create_conversation(tenant_id, to)
            
            # Insertar mensaje
            query = """
                INSERT INTO WhatsApp_Messages 
                (conversation_id, tenant_id, wa_message_id, wa_from_number, wa_to_number, 
                 wa_message_type, wa_message_content, wa_direction, wa_status, wa_timestamp,
                 template_name, media_url, caption)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s)
            """
            
            cursor.execute(query, (
                conversation_id, tenant_id, whatsapp_message_id, 
                config.get('wa_phone_number_id', ''), to, message_type, 
                message, 'outbound', status, template_name, media_url, caption
            ))
            
            # Actualizar conversación
            self._update_conversation_last_message(conversation_id, message, message_type)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Mensaje saliente guardado: {whatsapp_message_id}")
            
        except Exception as e:
            logger.error(f"Error guardando mensaje saliente: {e}")
    
    def _get_or_create_conversation(self, tenant_id: int, phone_number: str) -> int:
        """Obtiene o crea una conversación para un número de teléfono"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Buscar conversación existente
            query = """
                SELECT id FROM WhatsApp_Conversations 
                WHERE tenant_id = %s AND wa_contact_phone = %s
            """
            cursor.execute(query, (tenant_id, phone_number))
            result = cursor.fetchone()
            
            if result:
                conversation_id = result[0]
            else:
                # Crear nueva conversación
                insert_query = """
                    INSERT INTO WhatsApp_Conversations 
                    (tenant_id, wa_contact_phone, wa_contact_name, wa_last_message, 
                     wa_last_message_type, wa_unread_count, wa_status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """
                cursor.execute(insert_query, (
                    tenant_id, phone_number, phone_number, '', '', 0, 'active'
                ))
                conversation_id = cursor.lastrowid
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error gestionando conversación: {e}")
            return None
    
    def _update_conversation_last_message(self, conversation_id: int, 
                                        message: str, message_type: str):
        """Actualiza el último mensaje de una conversación"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = """
                UPDATE WhatsApp_Conversations 
                SET wa_last_message = %s, wa_last_message_type = %s, 
                    wa_last_activity = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (message, message_type, conversation_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error actualizando conversación: {e}")

# Instancia global del manager
api_manager = WhatsAppBusinessAPIManager()

# Funciones de conveniencia para usar desde app.py
def send_whatsapp_message(tenant_id: int, to: str, message: str, 
                         message_type: str = 'text', **kwargs) -> Dict:
    """
    Función de conveniencia para enviar mensajes
    
    Args:
        tenant_id: ID del tenant
        to: Número de teléfono destino
        message: Contenido del mensaje
        message_type: Tipo de mensaje (text, template, image, document, etc.)
        **kwargs: Parámetros adicionales según el tipo de mensaje
    
    Returns:
        Dict con el resultado del envío
    """
    if message_type == 'text':
        return api_manager.send_text_message(tenant_id, to, message, 
                                           kwargs.get('reply_to_message_id'))
    elif message_type == 'template':
        return api_manager.send_template_message(tenant_id, to, message, 
                                               kwargs.get('template_params'))
    elif message_type in ['image', 'document', 'audio', 'video']:
        return api_manager.send_media_message(tenant_id, to, message_type, 
                                            kwargs.get('media_url'), 
                                            kwargs.get('caption'))
    else:
        return {
            "status": "error",
            "error": f"Tipo de mensaje no soportado: {message_type}"
        }

def get_whatsapp_message_status(tenant_id: int, message_id: str) -> Dict:
    """Obtiene el estado de un mensaje"""
    return api_manager.get_message_status(tenant_id, message_id)