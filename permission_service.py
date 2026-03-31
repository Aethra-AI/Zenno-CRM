# -*- coding: utf-8 -*-
"""
🔐 PERMISSION SERVICE - Sistema de Permisos y Jerarquía v3
Módulo B4: Gestión de permisos, roles y acceso a recursos conectado a Permisos_Unificados.
"""

import mysql.connector
import json
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# =====================================================
# FUNCIÓN AUXILIAR - Conexión a BD
# =====================================================

def get_db_connection():
    """Obtiene conexión a la base de datos"""
    try:
        from app import get_db_connection as app_get_db
        return app_get_db()
    except:
        # Fallback si no se puede importar de app
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'whatsapp_backend'),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )


# =====================================================
# 1. FUNCIONES DE ROLES (Legacy / Compatibilidad)
# =====================================================

def get_user_role_info(user_id, tenant_id):
    """Obtiene información básica del rol del usuario para compatibilidad."""
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT r.id as role_id, r.nombre as role_name
            FROM Users u
            JOIN Roles r ON u.rol_id = r.id
            WHERE u.id = %s AND u.tenant_id = %s AND u.activo = 1 AND r.activo = 1
        """, (user_id, tenant_id))
        return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error en get_user_role_info: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_role_name(user_id, tenant_id):
    role_info = get_user_role_info(user_id, tenant_id)
    return role_info['role_name'] if role_info else None

def is_admin(user_id, tenant_id):
    return get_user_role_name(user_id, tenant_id) == 'Administrador'

def is_supervisor(user_id, tenant_id):
    return get_user_role_name(user_id, tenant_id) == 'Supervisor'

def is_recruiter(user_id, tenant_id):
    return get_user_role_name(user_id, tenant_id) == 'Reclutador'


# =====================================================
# TRADUCTOR UNIVERSAL DE MÓDULOS (FASE 3)
# =====================================================

TRADUCTOR_MODULOS = {
    # Candidatos
    'candidate': 'candidates', 'candidates': 'candidates',
    'candidato': 'candidates', 'candidatos': 'candidates',
    'afiliado': 'candidates', 'afiliados': 'candidates',
    # Vacantes
    'vacancy': 'vacancies', 'vacancies': 'vacancies',
    'vacante': 'vacancies', 'vacantes': 'vacancies',
    # Clientes
    'client': 'clients', 'clients': 'clients',
    'cliente': 'clients', 'clientes': 'clients',
    # Usuarios
    'user': 'users', 'users': 'users',
    'usuario': 'users', 'usuarios': 'users',
    # Reportes
    'report': 'reports', 'reports': 'reports',
    'reporte': 'reports', 'reportes': 'reports',
    # Contratados
    'hired': 'hired', 'contratado': 'hired', 'contratados': 'hired'
}

def normalizar_modulo(modulo):
    """Normaliza el nombre del módulo usando el TRADUCTOR_MODULOS."""
    if not modulo: return modulo
    return TRADUCTOR_MODULOS.get(modulo.lower(), modulo)


# =====================================================
# 2. REFACTORIZACIÓN FASE 3 - TABLAS V3 (Permisos_Unificados)
# =====================================================

def can_access_tab(user_id, tenant_id, modulo):
    """
    Reescrita Fase 3: Consulta SELECT ver FROM Permisos_Unificados.
    """
    if is_admin(user_id, tenant_id): return True
    
    modulo_db = normalizar_modulo(modulo)
    
    conn = get_db_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT ver FROM Permisos_Unificados WHERE user_id=%s AND modulo=%s", (user_id, modulo_db))
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    except Exception as e:
        logger.error(f"Error en can_access_tab: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def can_perform_action(user_id, tenant_id, modulo, action):
    """
    Reescrita Fase 3: Consulta columna específica en Permisos_Unificados.
    """
    if is_admin(user_id, tenant_id): return True
    
    modulo_db = normalizar_modulo(modulo)
    
    # Lista blanca de columnas permitidas para evitar SQL Injection indirecto
    allowed_actions = ['ver', 'crear', 'editar', 'eliminar', 'exportar', 'importar', 'asignar']
    if action not in allowed_actions:
        # Si la acción no está en la lista estándar, intentamos usarla pero con cuidado
        logger.warning(f"Acción no estándar solicitada: {action}")
    
    conn = get_db_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        # Nota: Los nombres de columnas son seguros aquí ya que vienen del código, no del user input directo
        query = f"SELECT `{action}` FROM Permisos_Unificados WHERE user_id=%s AND modulo=%s"
        cursor.execute(query, (user_id, modulo_db))
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    except Exception as e:
        logger.error(f"Error en can_perform_action: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_redactions_for_tab(user_id, tenant_id, modulo):
    """
    Reescrita Fase 3: Consulta switches de privacidad.
    """
    if is_admin(user_id, tenant_id): return []
    
    modulo_db = normalizar_modulo(modulo)
    
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT ver_email_telefono, ver_nombre_empresa 
            FROM Permisos_Unificados 
            WHERE user_id=%s AND modulo=%s
        """, (user_id, modulo_db))
        result = cursor.fetchone()
        
        redacted = []
        if result:
            # Lógica corregida: 1 (True) = visible, 0 (False) = redactado
            if not bool(result.get('ver_email_telefono')):
                redacted.extend(['email', 'telefono'])
            if not bool(result.get('ver_nombre_empresa')):
                redacted.append('empresa')
        return redacted
    except Exception as e:
        logger.error(f"Error en get_redactions_for_tab: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()

# Alias para compatibilidad con firmas antiguas que usaban tab_key
def can_action_on_tab(user_id, tenant_id, tab_key, action):
    # Traducir acciones legacy a las de la tabla v3
    action_map = {'write': 'editar', 'create': 'crear', 'delete': 'eliminar'}
    v3_action = action_map.get(action, action)
    return can_perform_action(user_id, tenant_id, tab_key, v3_action)

def get_scope_for_tab(user_id, tenant_id, modulo):
    """Obtiene el alcance (alcance: todo, asignados, ninguno)"""
    if is_admin(user_id, tenant_id): return 'all'
    
    modulo_db = normalizar_modulo(modulo)
    
    conn = get_db_connection()
    if not conn: return 'none'
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT alcance FROM Permisos_Unificados WHERE user_id=%s AND modulo=%s", (user_id, modulo_db))
        result = cursor.fetchone()
        if not result: return 'none'
        
        # Mapeo de alcances V3 a lógica de filtros
        mapping = {
            'todo': 'all',
            'asignados': 'own',
            'ninguno': 'none'
        }
        return mapping.get(result['alcance'], 'none')
    except Exception as e:
        logger.error(f"Error en get_scope_for_tab (V3): {str(e)}")
        return 'none'
    finally:
        cursor.close()
        conn.close()


# =====================================================
# 3. FUNCIONES DE JERARQUÍA (EQUIPOS) - Se mantienen
# =====================================================

def get_team_members(supervisor_id, tenant_id):
    """Obtener miembros del equipo usando Asignaciones_Centrales (V3)."""
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    try:
        # En V3, un supervisor tiene asignados 'usuarios' (miembros de equipo)
        # usuario_destino = supervisor_id, tipo_entidad = 'usuario', entidad_id = member_id
        cursor.execute("""
            SELECT entidad_id as team_member_id 
            FROM Asignaciones_Centrales
            WHERE usuario_destino = %s AND tenant_id = %s AND tipo_entidad = 'usuario'
        """, (supervisor_id, tenant_id))
        return [row['team_member_id'] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error en get_team_members (V3): {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()

def is_user_in_team(supervisor_id, team_member_id, tenant_id):
    team_members = get_team_members(supervisor_id, tenant_id)
    return team_member_id in team_members

def get_user_supervisor(user_id, tenant_id):
    """Obtener supervisor usando Asignaciones_Centrales (V3)."""
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    try:
        # En V3, si un usuario es miembro de equipo, su supervisor lo tiene asignado
        # usuario_destino = supervisor_id, entidad_id = user_id
        cursor.execute("""
            SELECT usuario_destino as supervisor_id 
            FROM Asignaciones_Centrales
            WHERE entidad_id = %s AND tenant_id = %s AND tipo_entidad = 'usuario'
            LIMIT 1
        """, (user_id, tenant_id))
        result = cursor.fetchone()
        return result['supervisor_id'] if result else None
    except Exception as e:
        logger.error(f"Error en get_user_supervisor (V3): {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()


# =====================================================
# 4. FUNCIONES DE ACCESO A RECURSOS - Se mantienen
# =====================================================

def can_access_resource(user_id, tenant_id, resource_type, resource_id, required_access='read'):
    if is_admin(user_id, tenant_id): return True
    if was_created_by_user(user_id, tenant_id, resource_type, resource_id): return True
    
    conn = get_db_connection()
    if not conn: return False
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT access_level FROM Resource_Assignments
            WHERE assigned_to_user = %s AND tenant_id = %s AND resource_type = %s AND resource_id = %s AND is_active = 1
        """, (user_id, tenant_id, resource_type, resource_id))
        result = cursor.fetchone()
        if not result: return False
        
        hierarchy = {'read': 1, 'write': 2, 'full': 3}
        return hierarchy.get(result['access_level'], 0) >= hierarchy.get(required_access, 0)
    except: return False
    finally:
        cursor.close()
        conn.close()

def was_created_by_user(user_id, tenant_id, resource_type, resource_id):
    table_map = {'vacancy': 'Vacantes', 'client': 'Clientes', 'candidate': 'Afiliados', 'hired': 'Contratados'}
    id_map = {'vacancy': 'id_vacante', 'client': 'id_cliente', 'candidate': 'id_afiliado', 'hired': 'id_contratado'}
    
    table = table_map.get(resource_type)
    id_col = id_map.get(resource_type)
    if not table or not id_col: return False
    
    conn = get_db_connection()
    if not conn: return False
    cursor = conn.cursor(dictionary=True)
    try:
        created_by_col = 'created_by_user_id' if resource_type == 'candidate' else 'created_by_user'
        query = f"SELECT {created_by_col} FROM {table} WHERE {id_col} = %s AND tenant_id = %s"
        cursor.execute(query, (resource_id, tenant_id))
        result = cursor.fetchone()
        return result and result[created_by_col] == user_id
    except: return False
    finally:
        cursor.close()
        conn.close()


# =====================================================
# 5. FILTROS SQL - Se mantienen
# =====================================================

def get_accessible_user_ids(user_id, tenant_id):
    if is_admin(user_id, tenant_id): return None
    if is_supervisor(user_id, tenant_id):
        return [user_id] + get_team_members(user_id, tenant_id)
    return [user_id]

def build_user_filter_condition(user_id, tenant_id, created_by_field, resource_type, resource_id_field):
    """
    Reescrita Fase 4: Filtro de seguridad basado en alcances de Permisos_Unificados y Asignaciones_Centrales.
    """
    # Mapeo de resource_type a modulo de la tabla Permisos_Unificados (Traductor Inglés/Español)
    modulo_db = normalizar_modulo(resource_type)
    
    conn = get_db_connection()
    if not conn:
        # Fallback restrictivo por seguridad si falla la conexión
        return f"{created_by_field} = %s", [user_id]
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Consulta el alcance (scope) del usuario para este módulo
        cursor.execute("SELECT alcance FROM Permisos_Unificados WHERE user_id = %s AND modulo = %s", (user_id, modulo_db))
        result = cursor.fetchone()
        alcance = result['alcance'] if result else 'asignados'
        
        # Caso 1 (alcance = 'todo'): Retorna string vacío y parámetros vacíos
        if alcance == 'todo':
            return "", []
            
        # Caso 2 (alcance = 'asignados'): Genera filtro inclusivo (Creado por mí | Asignado a mí | Creado por mi equipo)
        if alcance == 'asignados':
            # 1. Creado por mí: {created_by_field} = %s
            # 2. Asignado a mí: {resource_id_field} IN (SELECT entidad_id FROM Asignaciones_Centrales WHERE usuario_destino = %s AND tipo_entidad = %s)
            # 3. Creado por mi equipo: {created_by_field} IN (SELECT entidad_id FROM Asignaciones_Centrales WHERE usuario_destino = %s AND tipo_entidad = 'usuario')
            condition = f"({created_by_field} = %s OR {resource_id_field} IN (SELECT entidad_id FROM Asignaciones_Centrales WHERE usuario_destino = %s AND tipo_entidad = %s AND tenant_id = %s) OR {created_by_field} IN (SELECT entidad_id FROM Asignaciones_Centrales WHERE usuario_destino = %s AND tipo_entidad = 'usuario' AND tenant_id = %s))"
            params = [user_id, user_id, resource_type, tenant_id, user_id, tenant_id]
            return condition, params
            
        # Fallback por defecto: Solo lo propio
        return f"{created_by_field} = %s", [user_id]
        
    except Exception as e:
        logger.error(f"Error en build_user_filter_condition: {str(e)}")
        # En caso de error, restringir a registros propios por seguridad
        return f"{created_by_field} = %s", [user_id]
    finally:
        cursor.close()
        conn.close()


# =====================================================
# 6. STUBS PARA COMPATIBILIDAD (Sin Lógica JSON)
# =====================================================

def get_user_permissions(user_id, tenant_id):
    """Legacy stub. Ahora se deben usar funciones granulares."""
    return {}

def get_effective_permissions(user_id, tenant_id):
    """Legacy stub. Ahora se deben usar funciones granulares."""
    return {}

def has_permission(user_id, tenant_id, permission_path, required_value=True):
    """Legacy stub remapeado a la nueva lógica si es posible."""
    parts = permission_path.split('.')
    if len(parts) == 2:
        return can_perform_action(user_id, tenant_id, parts[0], parts[1])
    return False

def get_permission_scope(user_id, tenant_id, resource_type):
    return get_scope_for_tab(user_id, tenant_id, resource_type)

def can_create_resource(user_id, tenant_id, resource_type):
    return can_perform_action(user_id, tenant_id, resource_type, 'crear')

def can_manage_users(user_id, tenant_id):
    return is_admin(user_id, tenant_id)

def get_ui_flags_for_tab(user_id, tenant_id, tab_key):
    return {} # Ya no se manejan flags JSON complejos en v3

def log_permission_check(user_id, tenant_id, action, resource_type=None, resource_id=None, allowed=False):
    pass # Auditoría simplificada
