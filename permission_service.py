# -*- coding: utf-8 -*-
"""
🔐 PERMISSION SERVICE - Sistema de Permisos y Jerarquía
Módulo B4: Gestión de permisos, roles y acceso a recursos

Jerarquía de roles:
- Administrador: Acceso total al tenant
- Supervisor: Acceso a su equipo y recursos asignados
- Reclutador: Solo sus propios recursos
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
# 1. FUNCIONES DE ROLES
# =====================================================

def get_user_role_info(user_id, tenant_id):
    """
    Obtiene información completa del rol del usuario.
    
    Returns:
        dict: {
            'role_id': int,
            'role_name': str,
            'permissions': dict
        }
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                r.id as role_id,
                r.nombre as role_name,
                r.permisos as permissions
            FROM Users u
            JOIN Roles r ON u.rol_id = r.id
            WHERE u.id = %s 
              AND u.tenant_id = %s 
              AND u.activo = 1
              AND r.activo = 1
        """, (user_id, tenant_id))
        
        result = cursor.fetchone()
        if result and result.get('permissions'):
            # Parsear JSON de permisos
            try:
                result['permissions'] = json.loads(result['permissions'])
            except:
                result['permissions'] = {}
        
        return result
    
    except Exception as e:
        logger.error(f"Error obteniendo rol del usuario: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_user_role_name(user_id, tenant_id):
    """
    Obtiene el nombre del rol del usuario.
    
    Returns:
        str: 'Administrador', 'Supervisor', 'Reclutador', o None
    """
    role_info = get_user_role_info(user_id, tenant_id)
    return role_info['role_name'] if role_info else None


def is_admin(user_id, tenant_id):
    """Verifica si el usuario es Administrador"""
    role_name = get_user_role_name(user_id, tenant_id)
    return role_name == 'Administrador'


def is_supervisor(user_id, tenant_id):
    """Verifica si el usuario es Supervisor"""
    role_name = get_user_role_name(user_id, tenant_id)
    return role_name == 'Supervisor'


def is_recruiter(user_id, tenant_id):
    """Verifica si el usuario es Reclutador"""
    role_name = get_user_role_name(user_id, tenant_id)
    return role_name == 'Reclutador'


# =====================================================
# 2. FUNCIONES DE PERMISOS
# =====================================================

def check_permission(user_id, tenant_id, permission_key):
    """
    Verifica si el usuario tiene un permiso específico.
    
    Args:
        user_id (int): ID del usuario
        tenant_id (int): ID del tenant
        permission_key (str): Clave del permiso a verificar
            Ejemplos: 'all', 'manage_users', 'create', 'edit_own', etc.
    
    Returns:
        bool: True si tiene el permiso, False si no
    """
    role_info = get_user_role_info(user_id, tenant_id)
    if not role_info:
        return False
    
    permissions = role_info.get('permissions', {})
    
    # Admin tiene acceso a todo
    if permissions.get('all') is True:
        return True
    
    # Verificar permiso específico
    return permissions.get(permission_key) is True


def get_user_permissions(user_id, tenant_id):
    """
    Obtiene todos los permisos del usuario (solo del rol, sin custom).
    Para permisos completos usar get_effective_permissions().
    
    Returns:
        dict: Diccionario de permisos del rol
    """
    role_info = get_user_role_info(user_id, tenant_id)
    return role_info.get('permissions', {}) if role_info else {}


# =====================================================
# 3. FUNCIONES DE JERARQUÍA (EQUIPOS)
# =====================================================

def get_team_members(supervisor_id, tenant_id):
    """
    Obtiene los IDs de los miembros del equipo de un supervisor.
    
    Returns:
        list: Lista de user_ids
    """
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT team_member_id
            FROM Team_Structure
            WHERE supervisor_id = %s 
              AND tenant_id = %s 
              AND is_active = 1
        """, (supervisor_id, tenant_id))
        
        results = cursor.fetchall()
        return [row['team_member_id'] for row in results]
    
    except Exception as e:
        logger.error(f"Error obteniendo miembros del equipo: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()


def is_user_in_team(supervisor_id, team_member_id, tenant_id):
    """Verifica si un usuario es miembro del equipo de un supervisor"""
    team_members = get_team_members(supervisor_id, tenant_id)
    return team_member_id in team_members


def get_user_supervisor(user_id, tenant_id):
    """
    Obtiene el supervisor del usuario (si tiene).
    
    Returns:
        int or None: ID del supervisor
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT supervisor_id
            FROM Team_Structure
            WHERE team_member_id = %s 
              AND tenant_id = %s 
              AND is_active = 1
            LIMIT 1
        """, (user_id, tenant_id))
        
        result = cursor.fetchone()
        return result['supervisor_id'] if result else None
    
    except Exception as e:
        logger.error(f"Error obteniendo supervisor: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()


# =====================================================
# 4. FUNCIONES DE ACCESO A RECURSOS
# =====================================================

def get_assigned_resources(user_id, tenant_id, resource_type=None):
    """
    Obtiene los recursos asignados a un usuario.
    
    Args:
        user_id (int): ID del usuario
        tenant_id (int): ID del tenant
        resource_type (str, optional): 'vacancy', 'client', 'candidate'
    
    Returns:
        list: Lista de dicts con información de recursos asignados
    """
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                resource_type,
                resource_id,
                access_level
            FROM Resource_Assignments
            WHERE assigned_to_user = %s 
              AND tenant_id = %s 
              AND is_active = 1
        """
        params = [user_id, tenant_id]
        
        if resource_type:
            query += " AND resource_type = %s"
            params.append(resource_type)
        
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    
    except Exception as e:
        logger.error(f"Error obteniendo recursos asignados: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()


def can_access_resource(user_id, tenant_id, resource_type, resource_id, required_access='read'):
    """
    Verifica si un usuario puede acceder a un recurso específico.
    
    Args:
        user_id (int): ID del usuario
        tenant_id (int): ID del tenant
        resource_type (str): 'vacancy', 'client', 'candidate'
        resource_id (int): ID del recurso
        required_access (str): 'read', 'write', 'full'
    
    Returns:
        bool: True si puede acceder, False si no
    """
    # Admin tiene acceso a todo
    if is_admin(user_id, tenant_id):
        return True
    
    # Verificar si el recurso fue creado por el usuario
    if was_created_by_user(user_id, tenant_id, resource_type, resource_id):
        return True
    
    # Verificar si el recurso está asignado al usuario
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT access_level
            FROM Resource_Assignments
            WHERE assigned_to_user = %s 
              AND tenant_id = %s 
              AND resource_type = %s
              AND resource_id = %s
              AND is_active = 1
        """, (user_id, tenant_id, resource_type, resource_id))
        
        result = cursor.fetchone()
        if not result:
            return False
        
        access_level = result['access_level']
        
        # Mapeo de niveles de acceso
        access_hierarchy = {
            'read': 1,
            'write': 2,
            'full': 3
        }
        
        user_level = access_hierarchy.get(access_level, 0)
        required_level = access_hierarchy.get(required_access, 0)
        
        return user_level >= required_level
    
    except Exception as e:
        logger.error(f"Error verificando acceso a recurso: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()


def was_created_by_user(user_id, tenant_id, resource_type, resource_id):
    """
    Verifica si un recurso fue creado por el usuario.
    
    Returns:
        bool: True si fue creado por el usuario
    """
    # Mapeo de tipos de recurso a tablas
    table_map = {
        'vacancy': 'Vacantes',
        'client': 'Clientes',
        'candidate': 'Afiliados',
        'hired': 'Contratados'  # 🔐 MÓDULO B10
    }
    
    table = table_map.get(resource_type)
    if not table:
        return False
    
    # Mapeo de nombres de columnas ID
    id_column_map = {
        'vacancy': 'id_vacante',
        'client': 'id_cliente',
        'candidate': 'id_afiliado',
        'hired': 'id_contratado'  # 🔐 MÓDULO B10
    }
    
    id_column = id_column_map.get(resource_type)
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    try:
        query = f"""
            SELECT created_by_user
            FROM {table}
            WHERE {id_column} = %s 
              AND tenant_id = %s
        """
        cursor.execute(query, (resource_id, tenant_id))
        
        result = cursor.fetchone()
        if not result:
            return False
        
        return result['created_by_user'] == user_id
    
    except Exception as e:
        logger.error(f"Error verificando creador del recurso: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()


# =====================================================
# 5. FUNCIONES DE FILTROS PARA QUERIES
# =====================================================

def get_accessible_user_ids(user_id, tenant_id):
    """
    Obtiene los IDs de usuarios cuya información puede ver el usuario actual.
    
    Para Admin: todos del tenant
    Para Supervisor: él mismo + su equipo
    Para Reclutador: solo él mismo
    
    Returns:
        list: Lista de user_ids accesibles
    """
    # Admin ve a todos
    if is_admin(user_id, tenant_id):
        return None  # None significa "todos"
    
    # Supervisor ve su equipo
    if is_supervisor(user_id, tenant_id):
        team_members = get_team_members(user_id, tenant_id)
        return [user_id] + team_members
    
    # Reclutador solo se ve a sí mismo
    return [user_id]


def build_user_filter_condition(user_id, tenant_id, created_by_column='created_by_user'):
    """
    Construye la condición SQL para filtrar por usuarios accesibles.
    
    Args:
        user_id (int): ID del usuario actual
        tenant_id (int): ID del tenant
        created_by_column (str): Nombre de la columna created_by_user
    
    Returns:
        tuple: (condition_str, params_list)
            - Admin: ("", []) - sin filtro adicional
            - Supervisor: ("created_by_user IN (%s, %s, %s)", [user_id, member1, member2])
            - Reclutador: ("created_by_user = %s", [user_id])
    """
    accessible_users = get_accessible_user_ids(user_id, tenant_id)
    
    # Admin: sin filtro
    if accessible_users is None:
        return ("", [])
    
    # Reclutador (solo 1 usuario)
    if len(accessible_users) == 1:
        return (f"{created_by_column} = %s", accessible_users)
    
    # Supervisor (varios usuarios)
    placeholders = ','.join(['%s'] * len(accessible_users))
    return (f"{created_by_column} IN ({placeholders})", accessible_users)


# =====================================================
# 6. FUNCIONES DE UTILIDAD
# =====================================================

def log_permission_check(user_id, tenant_id, action, resource_type=None, resource_id=None, allowed=False):
    """
    Registra un intento de acceso a un recurso (para auditoría).
    """
    try:
        conn = get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Permission_Audit_Log 
            (user_id, tenant_id, action, resource_type, resource_id, allowed, checked_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (user_id, tenant_id, action, resource_type, resource_id, allowed))
        conn.commit()
    except Exception as e:
        # No fallar si la tabla de auditoría no existe
        logger.debug(f"No se pudo registrar auditoría: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


# =====================================================
# 7. VERIFICACIÓN DE PERMISOS ESPECÍFICOS
# =====================================================

def can_create_resource(user_id, tenant_id, resource_type):
    """Verifica si el usuario puede crear un tipo de recurso"""
    # Admin siempre puede
    if is_admin(user_id, tenant_id):
        return True
    
    # Supervisor puede crear
    if is_supervisor(user_id, tenant_id):
        return check_permission(user_id, tenant_id, 'create')
    
    # Reclutador puede crear (sus propios recursos)
    if is_recruiter(user_id, tenant_id):
        return check_permission(user_id, tenant_id, 'create')
    
    return False


def can_manage_users(user_id, tenant_id):
    """Verifica si el usuario puede gestionar otros usuarios"""
    return check_permission(user_id, tenant_id, 'manage_users')


def can_assign_resources(user_id, tenant_id):
    """Verifica si el usuario puede asignar recursos a otros"""
    # Admin siempre puede
    if is_admin(user_id, tenant_id):
        return True
    
    # Supervisor puede asignar a su equipo
    if is_supervisor(user_id, tenant_id):
        return check_permission(user_id, tenant_id, 'assign_resources')
    
    return False


def can_view_reports(user_id, tenant_id, report_scope='own'):
    """
    Verifica si el usuario puede ver reportes.
    
    Args:
        report_scope (str): 'all', 'team', 'own'
    """
    if report_scope == 'all':
        return is_admin(user_id, tenant_id)
    
    if report_scope == 'team':
        return is_admin(user_id, tenant_id) or is_supervisor(user_id, tenant_id)
    
    if report_scope == 'own':
        return True  # Todos pueden ver sus propios reportes
    
    return False


# =====================================================
# EJEMPLO DE USO
# =====================================================

"""
# Verificar si usuario puede crear vacante
if can_create_resource(user_id, tenant_id, 'vacancy'):
    # Crear vacante...
    pass

# Obtener condición de filtro para query
condition, params = build_user_filter_condition(user_id, tenant_id)
if condition:
    query = f"SELECT * FROM Vacantes WHERE tenant_id = %s AND {condition}"
    cursor.execute(query, [tenant_id] + params)
else:
    query = "SELECT * FROM Vacantes WHERE tenant_id = %s"
    cursor.execute(query, [tenant_id])

# Verificar acceso a recurso específico
if can_access_resource(user_id, tenant_id, 'candidate', 123, 'write'):
    # Editar candidato...
    pass
"""


# =====================================================
# 8. PERMISOS GRANULARES Y PERSONALIZADOS
# =====================================================

def get_effective_permissions(user_id, tenant_id):
    """
    Obtiene los permisos efectivos del usuario.
    
    Lógica:
    1. Obtiene permisos base del Rol
    2. Obtiene custom_permissions del Usuario
    3. Merge: custom_permissions sobrescribe permisos del rol
    
    Returns:
        dict: Permisos efectivos completos
    """
    conn = get_db_connection()
    if not conn:
        return {}
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Obtener permisos del rol y custom del usuario
        cursor.execute("""
            SELECT 
                r.permisos as role_permissions,
                u.custom_permissions
            FROM Users u
            LEFT JOIN Roles r ON u.rol_id = r.id
            WHERE u.id = %s AND u.tenant_id = %s
        """, (user_id, tenant_id))
        
        result = cursor.fetchone()
        if not result:
            return {}
        
        # Parsear JSON
        role_perms = json.loads(result['role_permissions']) if result['role_permissions'] else {}
        custom_perms = json.loads(result['custom_permissions']) if result['custom_permissions'] else {}
        
        # Merge profundo: custom sobrescribe role
        effective_perms = deep_merge_permissions(role_perms, custom_perms)
        
        return effective_perms
    
    except Exception as e:
        logger.error(f"Error obteniendo permisos efectivos: {str(e)}")
        return {}
    finally:
        cursor.close()
        conn.close()


def deep_merge_permissions(base, override):
    """
    Merge profundo de dos diccionarios de permisos.
    override sobrescribe valores de base.
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Merge recursivo para diccionarios anidados
            result[key] = deep_merge_permissions(result[key], value)
        else:
            # Sobrescribir valor
            result[key] = value
    
    return result


def has_permission(user_id, tenant_id, permission_path, required_value=True):
    """
    Verifica si el usuario tiene un permiso específico.
    
    Args:
        permission_path: Ruta del permiso, ej: "candidates.create" o "dashboard.view_financial"
        required_value: Valor esperado (True por defecto)
    
    Returns:
        bool: True si tiene el permiso
    """
    # Admin siempre tiene acceso
    if is_admin(user_id, tenant_id):
        return True
    
    perms = get_effective_permissions(user_id, tenant_id)
    
    # Navegar por el path
    keys = permission_path.split('.')
    current = perms
    
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return False
        current = current[key]
    
    # Comparar valor
    if required_value is True:
        return current is True
    else:
        return current == required_value


def get_permission_scope(user_id, tenant_id, resource_type):
    """
    Obtiene el scope de visualización para un tipo de recurso.
    
    Returns:
        str: 'none', 'own', 'team', 'all'
    """
    if is_admin(user_id, tenant_id):
        return 'all'
    
    perms = get_effective_permissions(user_id, tenant_id)
    
    if resource_type in perms and isinstance(perms[resource_type], dict):
        return perms[resource_type].get('view_scope', 'none')
    
    return 'none'


def can_perform_action(user_id, tenant_id, resource_type, action):
    """
    Verifica si el usuario puede realizar una acción sobre un recurso.
    
    Returns:
        bool or str: True/False o scope
    """
    if is_admin(user_id, tenant_id):
        return True if not action.endswith('_scope') else 'all'
    
    perms = get_effective_permissions(user_id, tenant_id)
    
    if resource_type in perms and isinstance(perms[resource_type], dict):
        return perms[resource_type].get(action, False)
    
    return False


