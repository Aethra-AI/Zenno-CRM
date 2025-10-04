"""
📱 WHATSAPP WEBHOOK HANDLER - SISTEMA CENTRAL MULTI-TENANT
==========================================================

Este módulo maneja los webhooks de WhatsApp Business API
y los enruta al tenant correspondiente de forma segura.

Características:
- Identificación automática de tenant por phone_number_id
- Procesamiento de mensajes entrantes
- Logging completo de actividad
- Manejo de errores robusto
- Aislamiento completo por tenant
"""

import json
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, jsonify, Response
from whatsapp_config_manager import config_manager

# Configurar logging
logger = logging.getLogger(__name__)

class WhatsAppWebhookHandler:
    """
    Manejador de webhooks de WhatsApp Business API
    """
    
    def __init__(self):
        self.tenant_configs = {}
        self.load_tenant_configs()
    
    def load_tenant_configs(self):
        """Cargar configuraciones de tenant"""
        try:
            configs = config_manager.get_all_tenant_configs()
            for config in configs:
                if config['api_type'] == 'business_api' and config['phone_number_id']:
                    self.tenant_configs[config['phone_number_id']] = {
                        'tenant_id': config['tenant_id'],
                        'webhook_verify_token': config['webhook_verify_token']
                    }
            
            logger.info(f"✅ Cargadas {len(self.tenant_configs)} configuraciones de webhook")
            
        except Exception as e:
            logger.error(f"❌ Error cargando configuraciones: {str(e)}")
    
    def verify_webhook(self) -> Response:
        """
        Verificar webhook de WhatsApp (GET request)
        """
        try:
            # Parámetros de verificación de WhatsApp
            mode = request.args.get('hub.mode')
            token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            
            logger.info(f"🔍 Verificación webhook - Mode: {mode}, Token: {token}")
            
            # Verificar que sea una suscripción
            if mode != 'subscribe':
                logger.warning(f"⚠️ Modo de webhook inválido: {mode}")
                return Response('Forbidden', status=403)
            
            # Verificar token contra configuraciones de tenant
            valid_token = False
            for phone_number_id, config in self.tenant_configs.items():
                if config['webhook_verify_token'] == token:
                    valid_token = True
                    logger.info(f"✅ Token válido para tenant {config['tenant_id']} (phone: {phone_number_id})")
                    break
            
            if not valid_token:
                logger.warning(f"❌ Token de verificación inválido: {token}")
                return Response('Forbidden', status=403)
            
            # Retornar challenge
            logger.info(f"✅ Webhook verificado exitosamente - Challenge: {challenge}")
            return Response(challenge, status=200)
            
        except Exception as e:
            logger.error(f"❌ Error verificando webhook: {str(e)}")
            return Response('Internal Server Error', status=500)
    
    def process_webhook(self) -> Response:
        """
        Procesar webhook de WhatsApp (POST request)
        """
        try:
            # Obtener datos del webhook
            webhook_data = request.get_json()
            logger.info(f"📨 Webhook recibido: {json.dumps(webhook_data, indent=2)}")
            
            # Procesar entradas del webhook
            entries = webhook_data.get('entry', [])
            
            for entry in entries:
                # Obtener phone_number_id para identificar tenant
                phone_number_id = entry.get('id')
                
                if not phone_number_id:
                    logger.warning("⚠️ Webhook sin phone_number_id")
                    continue
                
                # Identificar tenant
                tenant_config = self.tenant_configs.get(phone_number_id)
                if not tenant_config:
                    logger.warning(f"⚠️ Phone number ID no encontrado: {phone_number_id}")
                    continue
                
                tenant_id = tenant_config['tenant_id']
                logger.info(f"🏢 Procesando webhook para tenant {tenant_id}")
                
                # Procesar cambios del webhook
                changes = entry.get('changes', [])
                for change in changes:
                    self.process_webhook_change(tenant_id, phone_number_id, change)
            
            return jsonify({'status': 'success'}), 200
            
        except Exception as e:
            logger.error(f"❌ Error procesando webhook: {str(e)}")
            return Response('Internal Server Error', status=500)
    
    def process_webhook_change(self, tenant_id: int, phone_number_id: str, change: Dict[str, Any]):
        """
        Procesar un cambio específico del webhook
        """
        try:
            field = change.get('field')
            value = change.get('value', {})
            
            logger.info(f"🔄 Procesando cambio - Field: {field}, Tenant: {tenant_id}")
            
            # Procesar según el tipo de campo
            if field == 'messages':
                self.process_message_webhook(tenant_id, phone_number_id, value)
            elif field == 'message_status':
                self.process_message_status_webhook(tenant_id, phone_number_id, value)
            elif field == 'account_update':
                self.process_account_update_webhook(tenant_id, phone_number_id, value)
            else:
                logger.info(f"ℹ️ Campo de webhook no manejado: {field}")
            
        except Exception as e:
            logger.error(f"❌ Error procesando cambio de webhook: {str(e)}")
    
    def process_message_webhook(self, tenant_id: int, phone_number_id: str, value: Dict[str, Any]):
        """
        Procesar webhook de mensajes entrantes
        """
        try:
            messages = value.get('messages', [])
            contacts = value.get('contacts', [])
            metadata = value.get('metadata', {})
            
            logger.info(f"📨 Procesando {len(messages)} mensajes para tenant {tenant_id}")
            
            # Crear mapeo de contactos
            contact_map = {}
            for contact in contacts:
                contact_map[contact['wa_id']] = contact
            
            # Procesar cada mensaje
            for message in messages:
                self.process_incoming_message(tenant_id, phone_number_id, message, contact_map, metadata)
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensajes: {str(e)}")
    
    def process_incoming_message(self, tenant_id: int, phone_number_id: str, 
                                message: Dict[str, Any], contact_map: Dict[str, Any], 
                                metadata: Dict[str, Any]):
        """
        Procesar un mensaje entrante individual
        """
        try:
            # Extraer información del mensaje
            message_id = message['id']
            from_wa_id = message['from']
            timestamp = message['timestamp']
            message_type = message['type']
            
            # Obtener información del contacto
            contact = contact_map.get(from_wa_id, {})
            contact_name = contact.get('profile', {}).get('name', '')
            contact_phone = contact.get('wa_id', from_wa_id)
            
            # Extraer contenido según el tipo de mensaje
            content = self.extract_message_content(message, message_type)
            
            logger.info(f"💬 Mensaje entrante - From: {contact_name} ({contact_phone}), Type: {message_type}")
            
            # Guardar en base de datos
            self.save_incoming_message(
                tenant_id=tenant_id,
                phone_number_id=phone_number_id,
                message_id=message_id,
                contact_phone=contact_phone,
                contact_name=contact_name,
                message_type=message_type,
                content=content,
                timestamp=timestamp,
                raw_message=message
            )
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje individual: {str(e)}")
    
    def extract_message_content(self, message: Dict[str, Any], message_type: str) -> str:
        """
        Extraer contenido del mensaje según su tipo
        """
        try:
            if message_type == 'text':
                return message.get('text', {}).get('body', '')
            elif message_type == 'image':
                return f"[Imagen] {message.get('image', {}).get('caption', '')}"
            elif message_type == 'document':
                return f"[Documento] {message.get('document', {}).get('filename', '')}"
            elif message_type == 'audio':
                return "[Audio]"
            elif message_type == 'video':
                return f"[Video] {message.get('video', {}).get('caption', '')}"
            elif message_type == 'location':
                location = message.get('location', {})
                return f"[Ubicación] {location.get('name', '')} ({location.get('latitude')}, {location.get('longitude')})"
            elif message_type == 'contact':
                return "[Contacto]"
            elif message_type == 'sticker':
                return "[Sticker]"
            else:
                return f"[{message_type.title()}]"
                
        except Exception as e:
            logger.error(f"❌ Error extrayendo contenido: {str(e)}")
            return f"[Error procesando {message_type}]"
    
    def process_message_status_webhook(self, tenant_id: int, phone_number_id: str, value: Dict[str, Any]):
        """
        Procesar webhook de estado de mensajes
        """
        try:
            statuses = value.get('statuses', [])
            
            for status in statuses:
                message_id = status['id']
                status_value = status['status']
                timestamp = status['timestamp']
                recipient_id = status['recipient_id']
                
                logger.info(f"📊 Estado de mensaje - ID: {message_id}, Status: {status_value}")
                
                # Actualizar estado en base de datos
                self.update_message_status(
                    tenant_id=tenant_id,
                    message_id=message_id,
                    status=status_value,
                    timestamp=timestamp,
                    recipient_id=recipient_id
                )
                
        except Exception as e:
            logger.error(f"❌ Error procesando estado de mensaje: {str(e)}")
    
    def process_account_update_webhook(self, tenant_id: int, phone_number_id: str, value: Dict[str, Any]):
        """
        Procesar webhook de actualización de cuenta
        """
        try:
            logger.info(f"🏢 Actualización de cuenta para tenant {tenant_id}")
            
            # Guardar actualización en base de datos
            self.save_account_update(
                tenant_id=tenant_id,
                phone_number_id=phone_number_id,
                update_data=value
            )
            
        except Exception as e:
            logger.error(f"❌ Error procesando actualización de cuenta: {str(e)}")
    
    def save_incoming_message(self, tenant_id: int, phone_number_id: str, message_id: str,
                             contact_phone: str, contact_name: str, message_type: str,
                             content: str, timestamp: str, raw_message: Dict[str, Any]):
        """
        Guardar mensaje entrante en base de datos
        """
        try:
            from app import get_db_connection
            
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Buscar o crear conversación
            conversation_id = self.get_or_create_conversation(
                cursor, tenant_id, contact_phone, contact_name
            )
            
            # Guardar mensaje
            cursor.execute("""
                INSERT INTO WhatsApp_Messages (
                    tenant_id, conversation_id, message_id, wa_message_id,
                    direction, message_type, content, status, timestamp, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                tenant_id, conversation_id, message_id, message_id,
                'inbound', message_type, content, 'delivered',
                datetime.fromtimestamp(int(timestamp))
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Mensaje guardado - Tenant: {tenant_id}, Message: {message_id}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando mensaje: {str(e)}")
    
    def update_message_status(self, tenant_id: int, message_id: str, status: str,
                             timestamp: str, recipient_id: str):
        """
        Actualizar estado de mensaje
        """
        try:
            from app import get_db_connection
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Mapear estado de WhatsApp a estado interno
            status_map = {
                'sent': 'sent',
                'delivered': 'delivered',
                'read': 'read',
                'failed': 'failed'
            }
            
            internal_status = status_map.get(status, 'sent')
            
            # Actualizar estado
            cursor.execute("""
                UPDATE WhatsApp_Messages 
                SET status = %s, updated_at = NOW()
                WHERE tenant_id = %s AND message_id = %s
            """, (internal_status, tenant_id, message_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Estado actualizado - Message: {message_id}, Status: {internal_status}")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando estado: {str(e)}")
    
    def save_account_update(self, tenant_id: int, phone_number_id: str, update_data: Dict[str, Any]):
        """
        Guardar actualización de cuenta
        """
        try:
            from app import get_db_connection
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Guardar actualización
            cursor.execute("""
                INSERT INTO WhatsApp_Webhooks (
                    tenant_id, webhook_type, phone_number_id, raw_data, processed
                ) VALUES (%s, %s, %s, %s, TRUE)
            """, (tenant_id, 'account_update', phone_number_id, json.dumps(update_data)))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Actualización de cuenta guardada - Tenant: {tenant_id}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando actualización: {str(e)}")
    
    def get_or_create_conversation(self, cursor, tenant_id: int, contact_phone: str, contact_name: str) -> int:
        """
        Obtener o crear conversación para un contacto
        """
        try:
            # Buscar conversación existente
            cursor.execute("""
                SELECT id FROM WhatsApp_Conversations 
                WHERE tenant_id = %s AND contact_phone = %s
            """, (tenant_id, contact_phone))
            
            result = cursor.fetchone()
            
            if result:
                return result['id']
            
            # Crear nueva conversación
            conversation_id = f"{tenant_id}_{contact_phone}_{int(datetime.now().timestamp())}"
            
            cursor.execute("""
                INSERT INTO WhatsApp_Conversations (
                    tenant_id, conversation_id, contact_phone, contact_name,
                    status, created_at
                ) VALUES (%s, %s, %s, %s, 'active', NOW())
            """, (tenant_id, conversation_id, contact_phone, contact_name))
            
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo/creando conversación: {str(e)}")
            raise


# =====================================================
# INSTANCIA GLOBAL
# =====================================================

# Instancia global del manejador de webhooks
webhook_handler = WhatsAppWebhookHandler()


# =====================================================
# FUNCIONES DE UTILIDAD
# =====================================================

def handle_whatsapp_webhook_get():
    """Manejador GET para webhooks de WhatsApp"""
    return webhook_handler.verify_webhook()

def handle_whatsapp_webhook_post():
    """Manejador POST para webhooks de WhatsApp"""
    return webhook_handler.process_webhook()
