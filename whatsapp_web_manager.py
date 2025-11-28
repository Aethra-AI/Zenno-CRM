"""
WhatsApp Web Manager - Multi-Tenant
===================================
Gestiona sesiones de WhatsApp Web.js de forma multi-tenant.
Se integra con el sistema de WhatsApp Business API para proporcionar
una solución híbrida según la configuración del tenant.
"""

import requests
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import mysql.connector
from mysql.connector import Error

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppWebManager:
    """Gestor de WhatsApp Web.js multi-tenant"""
    
    def __init__(self):
        self.node_bridge_url = "http://localhost:3000"  # URL del bridge.js
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'reclutamiento_db'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': int(os.getenv('DB_PORT', 3306))
        }
    
    def get_tenant_config(self, tenant_id: int) -> Optional[Dict]:
        """Obtiene la configuración de WhatsApp para un tenant específico"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT wa_api_type, wa_access_token, wa_phone_number_id, 
                       wa_webhook_url, wa_business_account_id, wa_active
                FROM WhatsApp_Config 
                WHERE tenant_id = %s AND wa_active = TRUE
            """
            cursor.execute(query, (tenant_id,))
            config = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return config
            
        except Error as e:
            logger.error(f"Error obteniendo configuración tenant {tenant_id}: {e}")
            return None
    
    def get_tenant_whatsapp_mode(self, tenant_id: int) -> str:
        """
        Determina el modo de WhatsApp para un tenant:
        - 'business_api': Usa WhatsApp Business API oficial
        - 'web_js': Usa WhatsApp Web.js
        - 'hybrid': Usa ambos según el contexto
        """
        try:
            config = self.get_tenant_config(tenant_id)
            
            if not config:
                logger.info(f"Tenant {tenant_id}: Sin configuración, usando WhatsApp Web.js por defecto")
                return 'web_js'
            
            api_type = config.get('wa_api_type', 'web_js')
            
            if api_type == 'business_api':
                # Verificar si el token es válido
                if config.get('wa_access_token') and config.get('wa_phone_number_id'):
                    logger.info(f"Tenant {tenant_id}: Configurado para WhatsApp Business API")
                    return 'business_api'
                else:
                    logger.warning(f"Tenant {tenant_id}: Business API configurado pero sin credenciales, usando Web.js")
                    return 'web_js'
            else:
                logger.info(f"Tenant {tenant_id}: Configurado para WhatsApp Web.js")
                return 'web_js'
                
        except Exception as e:
            logger.error(f"Error determinando modo WhatsApp para tenant {tenant_id}: {e}")
            return 'web_js'
    
    def initialize_web_session(self, tenant_id: int, user_id: int = None) -> Dict:
        """
        Inicializa una sesión de WhatsApp Web.js para un tenant
        
        Args:
            tenant_id: ID del tenant
            user_id: ID del usuario (opcional)
        
        Returns:
            Dict con el resultado de la inicialización
        """
        try:
            session_id = f"tenant-{tenant_id}-user-{user_id or 'default'}"
            
            payload = {
                "session_id": session_id,
                "tenant_id": str(tenant_id)
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': str(tenant_id)
            }
            
            response = requests.post(
                f"{self.node_bridge_url}/api/whatsapp/session/init",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Sesión WhatsApp Web inicializada para tenant {tenant_id}: {session_id}")
                
                # Guardar estado en BD
                self._save_web_session_status(tenant_id, session_id, 'initializing')
                
                return {
                    "status": "success",
                    "session_id": session_id,
                    "tenant_id": tenant_id,
                    "mode": "web_js",
                    "result": result
                }
            else:
                error_msg = f"Error inicializando sesión Web: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "error": error_msg
                }
                
        except Exception as e:
            error_msg = f"Error conectando con bridge WhatsApp Web: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def get_web_session_status(self, tenant_id: int) -> Dict:
        """Obtiene el estado de la sesión de WhatsApp Web.js"""
        try:
            # Buscar sesión activa para el tenant
            session_id = self._get_active_web_session_id(tenant_id)
            
            if not session_id:
                return {
                    "status": "no_session",
                    "message": "No hay sesión activa para este tenant"
                }
            
            headers = {
                'X-Tenant-ID': str(tenant_id)
            }
            
            # Consultar estado al bridge (Node.js) usando el nuevo endpoint
            response = requests.get(
                f"{self.node_bridge_url}/api/whatsapp/session/status",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # El nuevo endpoint devuelve { success: true, session: { ... } }
                session_data = result.get('session') or {}
                
                return {
                    "status": "success",
                    "session_status": session_data.get('status'),
                    "is_ready": session_data.get('isReady', False),
                    "qr_code": session_data.get('qrCode'),
                    "tenant_id": tenant_id,
                    "session_id": session_id
                }
            elif response.status_code == 404:
                # La sesión existe en BD pero no en el bridge (posible reinicio)
                return {
                    "status": "no_session",
                    "message": "No hay sesión activa (Bridge 404)"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Error obteniendo estado: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error conectando con bridge: {str(e)}"
            }
    
    def send_web_message(self, tenant_id: int, to: str, message: str, 
                        message_type: str = 'text', **kwargs) -> Dict:
        """
        Envía un mensaje a través de WhatsApp Web.js
        
        Args:
            tenant_id: ID del tenant
            to: Número de teléfono destino
            message: Contenido del mensaje
            message_type: Tipo de mensaje
            **kwargs: Parámetros adicionales
        
        Returns:
            Dict con el resultado del envío
        """
        try:
            # Verificar que hay una sesión activa
            session_status = self.get_web_session_status(tenant_id)
            
            if session_status.get('status') != 'success' or not session_status.get('is_ready'):
                return {
                    "status": "error",
                    "error": "No hay sesión de WhatsApp Web activa y lista para este tenant"
                }
            
            session_id = session_status.get('session_id')
            
            # Preparar payload según el tipo de mensaje
            if message_type == 'text':
                payload = {
                    "message": message,
                    "type": "text"
                }
            elif message_type in ['image', 'document', 'audio', 'video']:
                payload = {
                    "message": message,
                    "type": message_type,
                    "media_url": kwargs.get('media_url'),
                    "caption": kwargs.get('caption')
                }
            else:
                return {
                    "status": "error",
                    "error": f"Tipo de mensaje no soportado: {message_type}"
                }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': str(tenant_id)
            }
            
            response = requests.post(
                f"{self.node_bridge_url}/api/whatsapp/chats/{to}/messages",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Guardar mensaje en BD
                self._save_web_message(tenant_id, to, message, message_type, 'sent')
                
                return {
                    "status": "success",
                    "message_id": result.get('messageId'),
                    "mode": "web_js",
                    "result": result
                }
            else:
                error_msg = f"Error enviando mensaje Web: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "error": error_msg
                }
                
        except Exception as e:
            error_msg = f"Error enviando mensaje Web: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def get_web_chats(self, tenant_id: int) -> Dict:
        """Obtiene la lista de chats de WhatsApp Web.js"""
        try:
            headers = {
                'X-Tenant-ID': str(tenant_id)
            }
            
            response = requests.get(
                f"{self.node_bridge_url}/api/whatsapp/chats",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "chats": result.get('chats', []),
                    "mode": "web_js"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Error obteniendo chats: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error conectando con bridge: {str(e)}"
            }
    
    def close_web_session(self, tenant_id: int) -> Dict:
        """Cierra la sesión de WhatsApp Web.js"""
        try:
            session_id = self._get_active_web_session_id(tenant_id)
            
            if not session_id:
                return {
                    "status": "no_session",
                    "message": "No hay sesión activa para cerrar"
                }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': str(tenant_id)
            }
            
            response = requests.delete(
                f"{self.node_bridge_url}/api/whatsapp/session/close",
                json={"session_id": session_id},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # Actualizar estado en BD
                self._save_web_session_status(tenant_id, session_id, 'closed')
                
                return {
                    "status": "success",
                    "message": "Sesión cerrada exitosamente"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Error cerrando sesión: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error conectando con bridge: {str(e)}"
            }
    
    def _save_web_session_status(self, tenant_id: int, session_id: str, status: str):
        """Guarda el estado de la sesión Web en la base de datos"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Insertar o actualizar estado de sesión
            query = """
                INSERT INTO WhatsApp_Web_Sessions (tenant_id, session_id, status, created_at, updated_at)
                VALUES (%s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                status = VALUES(status),
                updated_at = NOW()
            """
            
            cursor.execute(query, (tenant_id, session_id, status))
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error guardando estado de sesión Web: {e}")
    
    def _get_active_web_session_id(self, tenant_id: int) -> Optional[str]:
        """Obtiene el ID de la sesión Web activa para un tenant"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT session_id FROM WhatsApp_Web_Sessions 
                WHERE tenant_id = %s AND status IN ('initializing', 'ready', 'connecting')
                ORDER BY updated_at DESC LIMIT 1
            """
            
            cursor.execute(query, (tenant_id,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return result['session_id'] if result else None
            
        except Exception as e:
            logger.error(f"Error obteniendo sesión activa: {e}")
            return None
    
    def _save_web_message(self, tenant_id: int, to: str, message: str, 
                         message_type: str, status: str):
        """Guarda un mensaje Web en la base de datos"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Buscar o crear conversación
            conversation_id = self._get_or_create_conversation(tenant_id, to)
            
            # Insertar mensaje
            query = """
                INSERT INTO WhatsApp_Messages 
                (conversation_id, tenant_id, wa_message_id, wa_from_number, wa_to_number, 
                 wa_message_type, wa_message_content, wa_direction, wa_status, wa_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            cursor.execute(query, (
                conversation_id, tenant_id, f"web_{int(datetime.now().timestamp())}",
                'web_js', to, message_type, message, 'outbound', status
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error guardando mensaje Web: {e}")
    
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

# Instancia global del manager
web_manager = WhatsAppWebManager()

# Funciones de conveniencia
def get_tenant_whatsapp_mode(tenant_id: int) -> str:
    """Obtiene el modo de WhatsApp para un tenant"""
    return web_manager.get_tenant_whatsapp_mode(tenant_id)

def initialize_whatsapp_web_session(tenant_id: int, user_id: int = None) -> Dict:
    """Inicializa una sesión de WhatsApp Web.js"""
    return web_manager.initialize_web_session(tenant_id, user_id)

def send_whatsapp_web_message(tenant_id: int, to: str, message: str, 
                             message_type: str = 'text', **kwargs) -> Dict:
    """Envía un mensaje a través de WhatsApp Web.js"""
    return web_manager.send_web_message(tenant_id, to, message, message_type, **kwargs)

def get_whatsapp_web_status(tenant_id: int) -> Dict:
    """Obtiene el estado de WhatsApp Web.js"""
    return web_manager.get_web_session_status(tenant_id)
