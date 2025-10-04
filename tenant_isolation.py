"""
Módulo para gestión de aislamiento por tenant
"""

from functools import wraps
from flask import g, jsonify
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'crm_database')
        )
    except Exception as e:
        print(f"Error conectando a BD: {e}")
        return None

def get_current_tenant_id():
    """Obtener tenant_id del usuario actual"""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.get('tenant_id')
    return None

def tenant_required(f):
    """Decorator para asegurar que el usuario pertenece a un tenant"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            return jsonify({
                'error': 'Acceso denegado: Usuario no pertenece a ningún tenant',
                'code': 'TENANT_REQUIRED'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    """Decorator para super administradores del sistema"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user:
            return jsonify({'error': 'No autenticado'}), 401
        
        user_role = g.current_user.get('rol')
        if user_role != 'SUPER_ADMIN':
            return jsonify({
                'error': 'Acceso denegado: Se requieren permisos de Super Administrador',
                'code': 'SUPER_ADMIN_REQUIRED'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

def tenant_admin_required(f):
    """Decorator para administradores de tenant"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user:
            return jsonify({'error': 'No autenticado'}), 401
        
        user_role = g.current_user.get('rol')
        if user_role not in ['SUPER_ADMIN', 'ADMIN_EMPRESA']:
            return jsonify({
                'error': 'Acceso denegado: Se requieren permisos de administrador',
                'code': 'ADMIN_REQUIRED'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

def add_tenant_filter(query, tenant_id, table_alias=''):
    """Agregar filtro de tenant a una consulta SQL"""
    if not tenant_id:
        return query
    
    # Si la consulta ya tiene WHERE, agregar AND
    if 'WHERE' in query.upper():
        return f"{query} AND {table_alias}tenant_id = %s"
    else:
        return f"{query} WHERE {table_alias}tenant_id = %s"

def verify_tenant_access(resource_id, resource_table, tenant_id):
    """Verificar que un recurso pertenece al tenant del usuario"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT id FROM {resource_table} WHERE id = %s AND tenant_id = %s", 
                      (resource_id, tenant_id))
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        print(f"Error verificando acceso: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_tenant_users(tenant_id):
    """Obtener usuarios de un tenant específico"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.id, u.email, u.nombre, tr.nombre_rol as rol, u.activo
            FROM Users u
            LEFT JOIN Tenant_Roles tr ON u.rol_id = tr.id_rol
            WHERE u.tenant_id = %s
        """, (tenant_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error obteniendo usuarios: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def create_tenant_user(tenant_id, email, nombre, rol_id, password_hash):
    """Crear usuario en un tenant específico"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Users (tenant_id, email, nombre, rol_id, password_hash, activo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (tenant_id, email, nombre, rol_id, password_hash, True))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creando usuario: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_tenant_stats(tenant_id):
    """Obtener estadísticas de un tenant"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    cursor = conn.cursor(dictionary=True)
    try:
        stats = {}
        
        # Usuarios activos
        cursor.execute("SELECT COUNT(*) as count FROM Users WHERE tenant_id = %s AND activo = 1", (tenant_id,))
        stats['usuarios_activos'] = cursor.fetchone()['count']
        
        # Candidatos
        cursor.execute("SELECT COUNT(*) as count FROM Afiliados WHERE tenant_id = %s", (tenant_id,))
        stats['candidatos'] = cursor.fetchone()['count']
        
        # Vacantes activas
        cursor.execute("SELECT COUNT(*) as count FROM Vacantes WHERE tenant_id = %s AND estado = 'Abierta'", (tenant_id,))
        stats['vacantes_activas'] = cursor.fetchone()['count']
        
        # Postulaciones del mes
        cursor.execute("""
            SELECT COUNT(*) as count FROM Postulaciones p
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE v.tenant_id = %s AND MONTH(p.fecha_aplicacion) = MONTH(CURDATE())
        """, (tenant_id,))
        stats['postulaciones_mes'] = cursor.fetchone()['count']
        
        return stats
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()
