"""
📱 WHATSAPP CONFIG MANAGER - GESTIÓN MULTI-TENANT
=================================================

Este módulo maneja la configuración de WhatsApp por tenant,
permitiendo a cada tenant configurar su propia instancia de
WhatsApp (Business API o WhatsApp Web).

Características:
- Gestión de configuración por tenant
- Validación de configuraciones
- Soporte para Business API y WhatsApp Web
- Caché de configuraciones para rendimiento
- Logging y auditoría
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from mysql.connector import connect
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppConfigManager:
    """
    Gestor de configuración de WhatsApp por tenant
    """
    
    def __init__(self):
        self.config_cache = {}
        self.cache_ttl = timedelta(minutes=5)
        self.cache_timestamps = {}
    
    def get_db_connection(self):
        """Obtener conexión a la base de datos"""
        try:
            return connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'crm_db'),
                charset='utf8mb4'
            )
        except Exception as e:
            logger.error(f"❌ Error conectando a BD: {str(e)}")
            raise
    
    def get_tenant_config(self, tenant_id: int, api_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Obtener configuración de WhatsApp para un tenant
        
        Args:
            tenant_id: ID del tenant
            api_type: Tipo de API ('business_api' o 'whatsapp_web')
        
        Returns:
            Configuración del tenant o None si no existe
        """
        try:
            # Verificar caché
            cache_key = f"{tenant_id}_{api_type}" if api_type else f"{tenant_id}_all"
            
            if self._is_cache_valid(cache_key):
                logger.info(f"📋 Configuración obtenida desde caché - Tenant: {tenant_id}")
                return self.config_cache.get(cache_key)
            
            # Obtener desde base de datos
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            if api_type:
                cursor.execute("""
                    SELECT * FROM WhatsApp_Config 
                    WHERE tenant_id = %s AND api_type = %s AND is_active = TRUE
                """, (tenant_id, api_type))
            else:
                cursor.execute("""
                    SELECT * FROM WhatsApp_Config 
                    WHERE tenant_id = %s AND is_active = TRUE
                """, (tenant_id,))
            
            configs = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Procesar configuraciones
            if api_type:
                config = configs[0] if configs else None
                self._update_cache(cache_key, config)
                return config
            else:
                # Retornar todas las configuraciones
                result = {}
                for config in configs:
                    result[config['api_type']] = config
                
                self._update_cache(cache_key, result)
                return result
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo configuración tenant {tenant_id}: {str(e)}")
            return None
    
    def create_tenant_config(self, tenant_id: int, config_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Crear nueva configuración de WhatsApp para un tenant
        
        Args:
            tenant_id: ID del tenant
            config_data: Datos de configuración
        
        Returns:
            Tuple[success, message]
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Validar configuración
            validation_result = self._validate_config(config_data)
            if not validation_result[0]:
                return False, validation_result[1]
            
            # Insertar configuración
            cursor.execute("""
                INSERT INTO WhatsApp_Config (
                    tenant_id, api_type, business_api_token, phone_number_id,
                    webhook_verify_token, business_account_id, web_session_id,
                    web_qr_code, web_status, webhook_url, is_active,
                    auto_reconnect, max_retries
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tenant_id,
                config_data.get('api_type'),
                config_data.get('business_api_token'),
                config_data.get('phone_number_id'),
                config_data.get('webhook_verify_token'),
                config_data.get('business_account_id'),
                config_data.get('web_session_id'),
                config_data.get('web_qr_code'),
                config_data.get('web_status', 'disconnected'),
                config_data.get('webhook_url'),
                config_data.get('is_active', True),
                config_data.get('auto_reconnect', True),
                config_data.get('max_retries', 3)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Limpiar caché
            self._clear_cache(tenant_id)
            
            logger.info(f"✅ Configuración creada exitosamente - Tenant: {tenant_id}")
            return True, "Configuración creada exitosamente"
            
        except Exception as e:
            logger.error(f"❌ Error creando configuración tenant {tenant_id}: {str(e)}")
            return False, f"Error creando configuración: {str(e)}"
    
    def update_tenant_config(self, tenant_id: int, api_type: str, config_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Actualizar configuración de WhatsApp para un tenant
        
        Args:
            tenant_id: ID del tenant
            api_type: Tipo de API
            config_data: Datos de configuración
        
        Returns:
            Tuple[success, message]
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Validar configuración
            validation_result = self._validate_config(config_data)
            if not validation_result[0]:
                return False, validation_result[1]
            
            # Construir query de actualización dinámicamente
            update_fields = []
            update_values = []
            
            for field, value in config_data.items():
                if field in ['business_api_token', 'phone_number_id', 'webhook_verify_token', 
                           'business_account_id', 'web_session_id', 'web_qr_code', 'web_status',
                           'webhook_url', 'is_active', 'auto_reconnect', 'max_retries']:
                    update_fields.append(f"{field} = %s")
                    update_values.append(value)
            
            if not update_fields:
                return False, "No hay campos válidos para actualizar"
            
            update_values.extend([tenant_id, api_type])
            
            cursor.execute(f"""
                UPDATE WhatsApp_Config 
                SET {', '.join(update_fields)}, updated_at = NOW()
                WHERE tenant_id = %s AND api_type = %s
            """, update_values)
            
            if cursor.rowcount == 0:
                return False, "Configuración no encontrada"
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Limpiar caché
            self._clear_cache(tenant_id)
            
            logger.info(f"✅ Configuración actualizada exitosamente - Tenant: {tenant_id}")
            return True, "Configuración actualizada exitosamente"
            
        except Exception as e:
            logger.error(f"❌ Error actualizando configuración tenant {tenant_id}: {str(e)}")
            return False, f"Error actualizando configuración: {str(e)}"
    
    def delete_tenant_config(self, tenant_id: int, api_type: str) -> Tuple[bool, str]:
        """
        Eliminar configuración de WhatsApp para un tenant
        
        Args:
            tenant_id: ID del tenant
            api_type: Tipo de API
        
        Returns:
            Tuple[success, message]
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM WhatsApp_Config 
                WHERE tenant_id = %s AND api_type = %s
            """, (tenant_id, api_type))
            
            if cursor.rowcount == 0:
                return False, "Configuración no encontrada"
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Limpiar caché
            self._clear_cache(tenant_id)
            
            logger.info(f"✅ Configuración eliminada exitosamente - Tenant: {tenant_id}")
            return True, "Configuración eliminada exitosamente"
            
        except Exception as e:
            logger.error(f"❌ Error eliminando configuración tenant {tenant_id}: {str(e)}")
            return False, f"Error eliminando configuración: {str(e)}"
    
    def test_tenant_config(self, tenant_id: int, api_type: str) -> Tuple[bool, str]:
        """
        Probar configuración de WhatsApp para un tenant
        
        Args:
            tenant_id: ID del tenant
            api_type: Tipo de API
        
        Returns:
            Tuple[success, message]
        """
        try:
            config = self.get_tenant_config(tenant_id, api_type)
            if not config:
                return False, "Configuración no encontrada"
            
            if api_type == 'business_api':
                return self._test_business_api_config(config)
            elif api_type == 'whatsapp_web':
                return self._test_whatsapp_web_config(config)
            else:
                return False, "Tipo de API no válido"
                
        except Exception as e:
            logger.error(f"❌ Error probando configuración tenant {tenant_id}: {str(e)}")
            return False, f"Error probando configuración: {str(e)}"
    
    def get_all_tenant_configs(self) -> List[Dict[str, Any]]:
        """
        Obtener todas las configuraciones de WhatsApp
        
        Returns:
            Lista de configuraciones
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT wc.*, t.nombre_empresa 
                FROM WhatsApp_Config wc
                JOIN Tenants t ON wc.tenant_id = t.id
                WHERE wc.is_active = TRUE
                ORDER BY wc.tenant_id, wc.api_type
            """)
            
            configs = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            logger.info(f"📊 Obtenidas {len(configs)} configuraciones de WhatsApp")
            return configs
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo todas las configuraciones: {str(e)}")
            return []
    
    def get_tenant_stats(self, tenant_id: int) -> Dict[str, Any]:
        """
        Obtener estadísticas de WhatsApp para un tenant
        
        Args:
            tenant_id: ID del tenant
        
        Returns:
            Estadísticas del tenant
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Obtener configuración
            config = self.get_tenant_config(tenant_id)
            
            # Obtener estadísticas de conversaciones
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_conversations,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_conversations,
                    SUM(unread_count) as total_unread
                FROM WhatsApp_Conversations 
                WHERE tenant_id = %s
            """, (tenant_id,))
            
            conv_stats = cursor.fetchone()
            
            # Obtener estadísticas de mensajes
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN direction = 'inbound' THEN 1 END) as messages_received,
                    COUNT(CASE WHEN direction = 'outbound' THEN 1 END) as messages_sent,
                    COUNT(CASE WHEN DATE(created_at) = CURDATE() THEN 1 END) as messages_today
                FROM WhatsApp_Messages wm
                JOIN WhatsApp_Conversations wc ON wm.conversation_id = wc.id
                WHERE wc.tenant_id = %s
            """, (tenant_id,))
            
            msg_stats = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return {
                'config': config,
                'conversations': conv_stats,
                'messages': msg_stats,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas tenant {tenant_id}: {str(e)}")
            return {}
    
    def _validate_config(self, config_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validar datos de configuración
        
        Args:
            config_data: Datos de configuración
        
        Returns:
            Tuple[is_valid, error_message]
        """
        try:
            api_type = config_data.get('api_type')
            
            if api_type == 'business_api':
                required_fields = ['business_api_token', 'phone_number_id']
                for field in required_fields:
                    if not config_data.get(field):
                        return False, f"Campo requerido faltante: {field}"
                
                # Validar formato de token
                token = config_data.get('business_api_token')
                if not token.startswith('EAA'):
                    return False, "Token de API inválido"
                
            elif api_type == 'whatsapp_web':
                # Para WhatsApp Web no hay campos obligatorios
                pass
            
            else:
                return False, "Tipo de API no válido"
            
            return True, "Configuración válida"
            
        except Exception as e:
            return False, f"Error validando configuración: {str(e)}"
    
    def _test_business_api_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Probar configuración de Business API
        
        Args:
            config: Configuración del tenant
        
        Returns:
            Tuple[success, message]
        """
        try:
            # Importar aquí para evitar dependencias circulares
            from whatsapp_business_api_manager import WhatsAppBusinessAPIManager
            
            api_manager = WhatsAppBusinessAPIManager()
            success, message = api_manager.test_connection(config['tenant_id'])
            
            return success, message
            
        except Exception as e:
            return False, f"Error probando Business API: {str(e)}"
    
    def _test_whatsapp_web_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Probar configuración de WhatsApp Web
        
        Args:
            config: Configuración del tenant
        
        Returns:
            Tuple[success, message]
        """
        try:
            # Para WhatsApp Web, verificar que la sesión existe
            if config.get('web_status') == 'connected':
                return True, "WhatsApp Web conectado"
            else:
                return False, "WhatsApp Web no conectado"
                
        except Exception as e:
            return False, f"Error probando WhatsApp Web: {str(e)}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verificar si el caché es válido"""
        if cache_key not in self.cache_timestamps:
            return False
        
        return datetime.now() - self.cache_timestamps[cache_key] < self.cache_ttl
    
    def _update_cache(self, cache_key: str, data: Any):
        """Actualizar caché"""
        self.config_cache[cache_key] = data
        self.cache_timestamps[cache_key] = datetime.now()
    
    def _clear_cache(self, tenant_id: int):
        """Limpiar caché para un tenant"""
        keys_to_remove = [key for key in self.config_cache.keys() if key.startswith(f"{tenant_id}_")]
        for key in keys_to_remove:
            self.config_cache.pop(key, None)
            self.cache_timestamps.pop(key, None)


# =====================================================
# INSTANCIA GLOBAL
# =====================================================

# Instancia global del gestor de configuración
config_manager = WhatsAppConfigManager()


# =====================================================
# FUNCIONES DE UTILIDAD
# =====================================================

def get_tenant_whatsapp_config(tenant_id: int, api_type: str = None) -> Optional[Dict[str, Any]]:
    """
    Función de utilidad para obtener configuración de un tenant
    
    Args:
        tenant_id: ID del tenant
        api_type: Tipo de API
    
    Returns:
        Configuración del tenant
    """
    return config_manager.get_tenant_config(tenant_id, api_type)

def create_tenant_whatsapp_config(tenant_id: int, config_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Función de utilidad para crear configuración de un tenant
    
    Args:
        tenant_id: ID del tenant
        config_data: Datos de configuración
    
    Returns:
        Tuple[success, message]
    """
    return config_manager.create_tenant_config(tenant_id, config_data)

def update_tenant_whatsapp_config(tenant_id: int, api_type: str, config_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Función de utilidad para actualizar configuración de un tenant
    
    Args:
        tenant_id: ID del tenant
        api_type: Tipo de API
        config_data: Datos de configuración
    
    Returns:
        Tuple[success, message]
    """
    return config_manager.update_tenant_config(tenant_id, api_type, config_data)


# =====================================================
# EJEMPLO DE USO
# =====================================================

if __name__ == "__main__":
    # Ejemplo de uso
    manager = WhatsAppConfigManager()
    
    # Crear configuración Business API
    config_data = {
        'api_type': 'business_api',
        'business_api_token': 'EAAxxxx...',
        'phone_number_id': '123456789012345',
        'business_account_id': '987654321098765',
        'webhook_verify_token': 'mi_token_secreto'
    }
    
    success, message = manager.create_tenant_config(1, config_data)
    
    if success:
        print(f"✅ {message}")
        
        # Obtener configuración
        config = manager.get_tenant_config(1, 'business_api')
        print(f"📋 Configuración obtenida: {config}")
        
        # Probar configuración
        test_success, test_message = manager.test_tenant_config(1, 'business_api')
        print(f"🔍 Test: {test_success} - {test_message}")
    else:
        print(f"❌ {message}")
