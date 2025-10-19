"""
Gestión de API Keys Públicas
Endpoints para crear, listar, actualizar y eliminar API Keys
"""

import secrets
import hashlib
import bcrypt
from datetime import datetime, timedelta
from flask import jsonify, request, g
import mysql.connector
import logging

logger = logging.getLogger(__name__)

def generate_api_key():
    """
    Genera una API Key única con el formato: hnm_live_[64 caracteres]
    """
    # Generar 48 bytes aleatorios (que darán 64 caracteres en hex)
    random_bytes = secrets.token_bytes(48)
    key_suffix = random_bytes.hex()[:64]
    
    return f"hnm_live_{key_suffix}"

def hash_api_key(api_key):
    """
    Hashea la API Key usando bcrypt
    """
    return bcrypt.hashpw(api_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_api_key(api_key, hashed):
    """
    Verifica si una API Key coincide con su hash
    """
    try:
        return bcrypt.checkpw(api_key.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

class APIKeysManager:
    """Gestor de API Keys para el CRM"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def create_api_key(self, tenant_id, nombre, descripcion=None, permisos=None, 
                      rate_limit_per_minute=100, rate_limit_per_day=10000,
                      created_by_user=None):
        """
        Crea una nueva API Key para un tenant
        
        Args:
            tenant_id: ID del tenant
            nombre: Nombre descriptivo de la API Key
            descripcion: Descripción del propósito
            permisos: Dict con permisos {"vacancies": true, "candidates": true}
            rate_limit_per_minute: Límite de requests por minuto
            rate_limit_per_day: Límite de requests por día
            created_by_user: ID del usuario que crea la key
            
        Returns:
            dict: {"success": bool, "api_key": str, "data": dict}
        """
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            # Generar la API Key
            api_key = generate_api_key()
            api_key_hash = hash_api_key(api_key)
            
            # Permisos por defecto
            if permisos is None:
                permisos = {
                    "vacancies": True,
                    "candidates": True
                }
            
            # Insertar en la base de datos
            cursor.execute("""
                INSERT INTO Tenant_API_Keys (
                    tenant_id,
                    api_key,
                    api_secret_hash,
                    nombre_descriptivo,
                    descripcion,
                    permisos,
                    rate_limit_per_minute,
                    rate_limit_per_day,
                    created_by_user,
                    activa
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tenant_id,
                api_key,
                api_key_hash,
                nombre,
                descripcion,
                str(permisos) if isinstance(permisos, dict) else permisos,
                rate_limit_per_minute,
                rate_limit_per_day,
                created_by_user,
                True
            ))
            
            self.conn.commit()
            api_key_id = cursor.lastrowid
            
            # Obtener los datos creados
            cursor.execute("""
                SELECT 
                    id,
                    nombre_descriptivo,
                    descripcion,
                    permisos,
                    rate_limit_per_minute,
                    rate_limit_per_day,
                    activa,
                    fecha_creacion
                FROM Tenant_API_Keys
                WHERE id = %s
            """, (api_key_id,))
            
            data = cursor.fetchone()
            cursor.close()
            
            logger.info(f"✅ API Key creada: {nombre} (ID: {api_key_id}) para tenant {tenant_id}")
            
            return {
                "success": True,
                "message": "API Key creada exitosamente",
                "api_key": api_key,  # Solo se muestra una vez
                "data": data
            }
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error creando API Key: {str(e)}")
            return {
                "success": False,
                "error": f"Error creando API Key: {str(e)}"
            }
    
    def list_api_keys(self, tenant_id):
        """
        Lista todas las API Keys de un tenant
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            dict: {"success": bool, "data": list}
        """
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    id,
                    CONCAT('hnm_live_', REPEAT('•', 20), SUBSTRING(api_key, -8)) as api_key_preview,
                    nombre_descriptivo,
                    descripcion,
                    permisos,
                    activa,
                    fecha_creacion,
                    fecha_expiracion,
                    ultimo_uso,
                    total_requests,
                    requests_exitosos,
                    requests_fallidos,
                    rate_limit_per_minute,
                    rate_limit_per_day
                FROM Tenant_API_Keys
                WHERE tenant_id = %s
                ORDER BY fecha_creacion DESC
            """, (tenant_id,))
            
            api_keys = cursor.fetchall()
            cursor.close()
            
            return {
                "success": True,
                "data": api_keys,
                "total": len(api_keys)
            }
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error listando API Keys: {str(e)}")
            return {
                "success": False,
                "error": f"Error listando API Keys: {str(e)}"
            }
    
    def get_api_key(self, api_key_id, tenant_id):
        """
        Obtiene los detalles de una API Key específica
        
        Args:
            api_key_id: ID de la API Key
            tenant_id: ID del tenant (para validar permisos)
            
        Returns:
            dict: {"success": bool, "data": dict}
        """
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    id,
                    CONCAT('hnm_live_', REPEAT('•', 20), SUBSTRING(api_key, -8)) as api_key_preview,
                    nombre_descriptivo,
                    descripcion,
                    permisos,
                    activa,
                    fecha_creacion,
                    fecha_expiracion,
                    ultimo_uso,
                    total_requests,
                    requests_exitosos,
                    requests_fallidos,
                    rate_limit_per_minute,
                    rate_limit_per_day
                FROM Tenant_API_Keys
                WHERE id = %s AND tenant_id = %s
            """, (api_key_id, tenant_id))
            
            api_key = cursor.fetchone()
            cursor.close()
            
            if not api_key:
                return {
                    "success": False,
                    "error": "API Key no encontrada"
                }
            
            return {
                "success": True,
                "data": api_key
            }
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error obteniendo API Key: {str(e)}")
            return {
                "success": False,
                "error": f"Error obteniendo API Key: {str(e)}"
            }
    
    def update_api_key(self, api_key_id, tenant_id, updates):
        """
        Actualiza una API Key
        
        Args:
            api_key_id: ID de la API Key
            tenant_id: ID del tenant
            updates: Dict con campos a actualizar
            
        Returns:
            dict: {"success": bool, "data": dict}
        """
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            # Campos permitidos para actualizar
            allowed_fields = [
                'nombre_descriptivo', 'descripcion', 'permisos',
                'activa', 'rate_limit_per_minute', 'rate_limit_per_day'
            ]
            
            # Construir query dinámicamente
            update_fields = []
            values = []
            
            for field in allowed_fields:
                if field in updates:
                    update_fields.append(f"{field} = %s")
                    values.append(updates[field])
            
            if not update_fields:
                return {
                    "success": False,
                    "error": "No hay campos para actualizar"
                }
            
            # Agregar tenant_id y api_key_id al final
            values.extend([tenant_id, api_key_id])
            
            query = f"""
                UPDATE Tenant_API_Keys
                SET {', '.join(update_fields)}
                WHERE tenant_id = %s AND id = %s
            """
            
            cursor.execute(query, values)
            self.conn.commit()
            
            if cursor.rowcount == 0:
                cursor.close()
                return {
                    "success": False,
                    "error": "API Key no encontrada o sin cambios"
                }
            
            cursor.close()
            
            logger.info(f"✅ API Key actualizada: ID {api_key_id}")
            
            # Obtener datos actualizados
            return self.get_api_key(api_key_id, tenant_id)
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error actualizando API Key: {str(e)}")
            return {
                "success": False,
                "error": f"Error actualizando API Key: {str(e)}"
            }
    
    def delete_api_key(self, api_key_id, tenant_id):
        """
        Elimina una API Key (soft delete - la desactiva)
        
        Args:
            api_key_id: ID de la API Key
            tenant_id: ID del tenant
            
        Returns:
            dict: {"success": bool}
        """
        try:
            cursor = self.conn.cursor()
            
            # Soft delete: solo desactivar
            cursor.execute("""
                UPDATE Tenant_API_Keys
                SET activa = FALSE
                WHERE id = %s AND tenant_id = %s
            """, (api_key_id, tenant_id))
            
            self.conn.commit()
            
            if cursor.rowcount == 0:
                cursor.close()
                return {
                    "success": False,
                    "error": "API Key no encontrada"
                }
            
            cursor.close()
            
            logger.info(f"✅ API Key desactivada: ID {api_key_id}")
            
            return {
                "success": True,
                "message": "API Key desactivada exitosamente"
            }
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error eliminando API Key: {str(e)}")
            return {
                "success": False,
                "error": f"Error eliminando API Key: {str(e)}"
            }
    
    def get_api_key_stats(self, api_key_id, tenant_id):
        """
        Obtiene estadísticas de uso de una API Key
        
        Args:
            api_key_id: ID de la API Key
            tenant_id: ID del tenant
            
        Returns:
            dict: {"success": bool, "stats": dict}
        """
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            # Estadísticas generales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN exitoso = 1 THEN 1 ELSE 0 END) as requests_exitosos,
                    SUM(CASE WHEN exitoso = 0 THEN 1 ELSE 0 END) as requests_fallidos,
                    AVG(response_time_ms) as avg_response_time,
                    MAX(timestamp) as ultimo_uso,
                    MIN(timestamp) as primer_uso
                FROM API_Key_Logs
                WHERE api_key_id = %s AND tenant_id = %s
            """, (api_key_id, tenant_id))
            
            stats = cursor.fetchone()
            
            # Requests por día (últimos 7 días)
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as fecha,
                    COUNT(*) as requests,
                    SUM(CASE WHEN exitoso = 1 THEN 1 ELSE 0 END) as exitosos
                FROM API_Key_Logs
                WHERE api_key_id = %s 
                  AND tenant_id = %s
                  AND timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(timestamp)
                ORDER BY fecha DESC
            """, (api_key_id, tenant_id))
            
            requests_por_dia = cursor.fetchall()
            
            # Endpoints más usados
            cursor.execute("""
                SELECT 
                    endpoint,
                    COUNT(*) as total,
                    SUM(CASE WHEN exitoso = 1 THEN 1 ELSE 0 END) as exitosos
                FROM API_Key_Logs
                WHERE api_key_id = %s AND tenant_id = %s
                GROUP BY endpoint
                ORDER BY total DESC
                LIMIT 10
            """, (api_key_id, tenant_id))
            
            endpoints_mas_usados = cursor.fetchall()
            
            cursor.close()
            
            return {
                "success": True,
                "stats": {
                    "general": stats,
                    "requests_por_dia": requests_por_dia,
                    "endpoints_mas_usados": endpoints_mas_usados
                }
            }
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error obteniendo estadísticas: {str(e)}")
            return {
                "success": False,
                "error": f"Error obteniendo estadísticas: {str(e)}"
            }
