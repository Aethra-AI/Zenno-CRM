"""
Servicio de gestión de API Keys públicas para Multi-Tenant
Permite a cada tenant crear y gestionar sus propias API Keys
para compartir datos de forma segura con aplicaciones externas.
"""

import os
import secrets
import hashlib
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import json

# Configurar logging
logger = logging.getLogger(__name__)

class PublicAPIService:
    """Servicio para gestionar API Keys públicas por tenant"""
    
    def __init__(self):
        """Inicializar servicio"""
        self.api_key_prefix = "hnm_live_"  # Prefijo para identificar las keys
        self.secret_length = 32  # Longitud del secreto en bytes
        
    def generate_api_key(self) -> str:
        """
        Generar una API Key única
        
        Returns:
            str: API Key en formato hnm_live_xxxxx
        """
        # Generar 32 bytes aleatorios y convertir a hexadecimal
        random_bytes = secrets.token_bytes(self.secret_length)
        key_suffix = random_bytes.hex()
        
        return f"{self.api_key_prefix}{key_suffix}"
    
    def hash_secret(self, secret: str) -> str:
        """
        Crear hash del secreto usando bcrypt
        
        Args:
            secret: Secreto a hashear
            
        Returns:
            str: Hash del secreto
        """
        # Convertir a bytes y hashear con bcrypt
        secret_bytes = secret.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(secret_bytes, salt)
        
        return hashed.decode('utf-8')
    
    def verify_secret(self, secret: str, hashed_secret: str) -> bool:
        """
        Verificar si un secreto coincide con su hash
        
        Args:
            secret: Secreto a verificar
            hashed_secret: Hash almacenado
            
        Returns:
            bool: True si coincide
        """
        try:
            secret_bytes = secret.encode('utf-8')
            hashed_bytes = hashed_secret.encode('utf-8')
            return bcrypt.checkpw(secret_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"Error verificando secreto: {str(e)}")
            return False
    
    def create_api_key(self, conn, tenant_id: int, nombre: str, 
                       descripcion: str = None, created_by_user: int = None,
                       permisos: Dict = None, dias_expiracion: int = None) -> Dict[str, Any]:
        """
        Crear una nueva API Key para un tenant
        
        Args:
            conn: Conexión a la base de datos
            tenant_id: ID del tenant
            nombre: Nombre descriptivo de la API Key
            descripcion: Descripción del propósito
            created_by_user: ID del usuario que crea la key
            permisos: Diccionario de permisos específicos
            dias_expiracion: Días hasta que expire (None = sin expiración)
            
        Returns:
            Dict con la API Key generada y su información
        """
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Generar API Key única
            api_key = self.generate_api_key()
            
            # Verificar que no exista (muy improbable, pero por seguridad)
            cursor.execute("SELECT id FROM Tenant_API_Keys WHERE api_key = %s", (api_key,))
            if cursor.fetchone():
                # Si existe, generar otra
                return self.create_api_key(conn, tenant_id, nombre, descripcion, 
                                          created_by_user, permisos, dias_expiracion)
            
            # Generar secreto (no se almacena, solo su hash)
            api_secret = secrets.token_urlsafe(48)  # 48 bytes = 64 caracteres en base64
            api_secret_hash = self.hash_secret(api_secret)
            
            # Calcular fecha de expiración
            fecha_expiracion = None
            if dias_expiracion:
                fecha_expiracion = datetime.now() + timedelta(days=dias_expiracion)
            
            # Permisos por defecto
            if permisos is None:
                permisos = {
                    "vacancies": True,
                    "candidates": True
                }
            
            # Insertar en base de datos
            sql = """
                INSERT INTO Tenant_API_Keys (
                    tenant_id, api_key, api_secret_hash, nombre_descriptivo,
                    descripcion, activa, fecha_expiracion, permisos, created_by_user
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (
                tenant_id,
                api_key,
                api_secret_hash,
                nombre,
                descripcion,
                True,  # activa por defecto
                fecha_expiracion,
                json.dumps(permisos),
                created_by_user
            ))
            
            conn.commit()
            api_key_id = cursor.lastrowid
            
            logger.info(f"API Key creada exitosamente para tenant {tenant_id}: {api_key[:20]}...")
            
            # Retornar información (incluyendo el secreto solo esta vez)
            return {
                'success': True,
                'api_key_id': api_key_id,
                'api_key': api_key,
                'api_secret': api_secret,  # ⚠️ Solo se muestra al crear, nunca más
                'nombre': nombre,
                'fecha_creacion': datetime.now().isoformat(),
                'fecha_expiracion': fecha_expiracion.isoformat() if fecha_expiracion else None,
                'permisos': permisos,
                'warning': '⚠️ IMPORTANTE: Guarda el API Secret en un lugar seguro. No podrás verlo nuevamente.'
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creando API Key: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            cursor.close()
    
    def validate_api_key(self, conn, api_key: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validar una API Key y obtener información del tenant
        
        Args:
            conn: Conexión a la base de datos
            api_key: API Key a validar
            
        Returns:
            Tuple (es_valida, datos_api_key)
        """
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Buscar la API Key
            sql = """
                SELECT 
                    id, tenant_id, api_key, api_secret_hash, nombre_descriptivo,
                    activa, fecha_expiracion, permisos, rate_limit_per_minute,
                    rate_limit_per_day, ultimo_uso, total_requests
                FROM Tenant_API_Keys
                WHERE api_key = %s
            """
            
            cursor.execute(sql, (api_key,))
            api_key_data = cursor.fetchone()
            
            if not api_key_data:
                logger.warning(f"API Key no encontrada: {api_key[:20]}...")
                return False, None
            
            # Verificar si está activa
            if not api_key_data['activa']:
                logger.warning(f"API Key inactiva: {api_key[:20]}...")
                return False, {'error': 'API Key desactivada'}
            
            # Verificar si ha expirado
            if api_key_data['fecha_expiracion']:
                if datetime.now() > api_key_data['fecha_expiracion']:
                    logger.warning(f"API Key expirada: {api_key[:20]}...")
                    return False, {'error': 'API Key expirada'}
            
            # Parsear permisos JSON
            if api_key_data['permisos']:
                try:
                    api_key_data['permisos'] = json.loads(api_key_data['permisos'])
                except:
                    api_key_data['permisos'] = {}
            
            # Actualizar último uso
            cursor.execute(
                "UPDATE Tenant_API_Keys SET ultimo_uso = NOW() WHERE id = %s",
                (api_key_data['id'],)
            )
            conn.commit()
            
            logger.info(f"API Key válida para tenant {api_key_data['tenant_id']}")
            
            return True, api_key_data
            
        except Exception as e:
            logger.error(f"Error validando API Key: {str(e)}")
            return False, None
        finally:
            cursor.close()
    
    def check_rate_limit(self, conn, api_key_id: int, rate_limit_per_minute: int) -> Tuple[bool, int]:
        """
        Verificar si la API Key ha excedido el rate limit
        
        Args:
            conn: Conexión a la base de datos
            api_key_id: ID de la API Key
            rate_limit_per_minute: Límite de requests por minuto
            
        Returns:
            Tuple (permitido, requests_restantes)
        """
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Ventana de tiempo: último minuto
            ventana_inicio = datetime.now().replace(second=0, microsecond=0)
            
            # Buscar o crear registro de rate limit
            sql = """
                SELECT request_count 
                FROM API_Key_Rate_Limits
                WHERE api_key_id = %s 
                AND ventana_inicio = %s 
                AND ventana_tipo = 'minute'
            """
            
            cursor.execute(sql, (api_key_id, ventana_inicio))
            result = cursor.fetchone()
            
            if result:
                current_count = result['request_count']
                
                if current_count >= rate_limit_per_minute:
                    logger.warning(f"Rate limit excedido para API Key {api_key_id}")
                    return False, 0
                
                # Incrementar contador
                cursor.execute("""
                    UPDATE API_Key_Rate_Limits 
                    SET request_count = request_count + 1
                    WHERE api_key_id = %s AND ventana_inicio = %s AND ventana_tipo = 'minute'
                """, (api_key_id, ventana_inicio))
                
                requests_restantes = rate_limit_per_minute - current_count - 1
            else:
                # Crear nuevo registro
                cursor.execute("""
                    INSERT INTO API_Key_Rate_Limits (api_key_id, ventana_inicio, ventana_tipo, request_count)
                    VALUES (%s, %s, 'minute', 1)
                """, (api_key_id, ventana_inicio))
                
                requests_restantes = rate_limit_per_minute - 1
            
            conn.commit()
            return True, requests_restantes
            
        except Exception as e:
            logger.error(f"Error verificando rate limit: {str(e)}")
            return True, rate_limit_per_minute  # En caso de error, permitir
        finally:
            cursor.close()
    
    def log_api_request(self, conn, api_key_id: int, tenant_id: int,
                       endpoint: str, metodo: str, status_code: int,
                       ip_origen: str, user_agent: str = None,
                       query_params: Dict = None, error_message: str = None,
                       response_time_ms: int = None):
        """
        Registrar uso de la API Key para auditoría
        
        Args:
            conn: Conexión a la base de datos
            api_key_id: ID de la API Key
            tenant_id: ID del tenant
            endpoint: Endpoint accedido
            metodo: Método HTTP (GET, POST, etc.)
            status_code: Código de respuesta HTTP
            ip_origen: IP desde donde se hizo la petición
            user_agent: User agent del cliente
            query_params: Parámetros de la petición
            error_message: Mensaje de error si falló
            response_time_ms: Tiempo de respuesta en ms
        """
        try:
            cursor = conn.cursor()
            
            exitoso = 200 <= status_code < 300
            
            sql = """
                INSERT INTO API_Key_Logs (
                    api_key_id, tenant_id, endpoint, metodo, status_code,
                    exitoso, ip_origen, user_agent, query_params,
                    error_message, response_time_ms
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (
                api_key_id,
                tenant_id,
                endpoint,
                metodo,
                status_code,
                exitoso,
                ip_origen,
                user_agent,
                json.dumps(query_params) if query_params else None,
                error_message,
                response_time_ms
            ))
            
            # Actualizar contador en la API Key
            if exitoso:
                cursor.execute("""
                    UPDATE Tenant_API_Keys 
                    SET total_requests = total_requests + 1,
                        requests_exitosos = requests_exitosos + 1
                    WHERE id = %s
                """, (api_key_id,))
            else:
                cursor.execute("""
                    UPDATE Tenant_API_Keys 
                    SET total_requests = total_requests + 1,
                        requests_fallidos = requests_fallidos + 1
                    WHERE id = %s
                """, (api_key_id,))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error registrando log de API: {str(e)}")
        finally:
            cursor.close()
    
    def get_api_keys_by_tenant(self, conn, tenant_id: int) -> List[Dict]:
        """
        Obtener todas las API Keys de un tenant
        
        Args:
            conn: Conexión a la base de datos
            tenant_id: ID del tenant
            
        Returns:
            Lista de API Keys
        """
        try:
            cursor = conn.cursor(dictionary=True)
            
            sql = """
                SELECT 
                    id, api_key, nombre_descriptivo, descripcion,
                    activa, fecha_creacion, fecha_expiracion, ultimo_uso,
                    total_requests, requests_exitosos, requests_fallidos,
                    rate_limit_per_minute, permisos
                FROM Tenant_API_Keys
                WHERE tenant_id = %s
                ORDER BY fecha_creacion DESC
            """
            
            cursor.execute(sql, (tenant_id,))
            api_keys = cursor.fetchall()
            
            # Parsear permisos JSON
            for key in api_keys:
                if key['permisos']:
                    try:
                        key['permisos'] = json.loads(key['permisos'])
                    except:
                        key['permisos'] = {}
                
                # Ocultar parte de la API Key por seguridad
                if key['api_key']:
                    key['api_key_preview'] = key['api_key'][:20] + '...'
            
            return api_keys
            
        except Exception as e:
            logger.error(f"Error obteniendo API Keys: {str(e)}")
            return []
        finally:
            cursor.close()
    
    def deactivate_api_key(self, conn, api_key_id: int, tenant_id: int) -> bool:
        """
        Desactivar una API Key
        
        Args:
            conn: Conexión a la base de datos
            api_key_id: ID de la API Key
            tenant_id: ID del tenant (para verificar pertenencia)
            
        Returns:
            bool: True si se desactivó correctamente
        """
        try:
            cursor = conn.cursor()
            
            sql = """
                UPDATE Tenant_API_Keys 
                SET activa = FALSE 
                WHERE id = %s AND tenant_id = %s
            """
            
            cursor.execute(sql, (api_key_id, tenant_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"API Key {api_key_id} desactivada para tenant {tenant_id}")
                return True
            
            return False
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error desactivando API Key: {str(e)}")
            return False
        finally:
            cursor.close()
    
    def delete_api_key(self, conn, api_key_id: int, tenant_id: int) -> bool:
        """
        Eliminar una API Key permanentemente
        
        Args:
            conn: Conexión a la base de datos
            api_key_id: ID de la API Key
            tenant_id: ID del tenant (para verificar pertenencia)
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            cursor = conn.cursor()
            
            sql = """
                DELETE FROM Tenant_API_Keys 
                WHERE id = %s AND tenant_id = %s
            """
            
            cursor.execute(sql, (api_key_id, tenant_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"API Key {api_key_id} eliminada para tenant {tenant_id}")
                return True
            
            return False
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error eliminando API Key: {str(e)}")
            return False
        finally:
            cursor.close()

# Instancia global del servicio
public_api_service = PublicAPIService()
