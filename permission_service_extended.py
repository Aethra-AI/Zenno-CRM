# -*- coding: utf-8 -*-
"""
🔐 EXTENSIÓN DE PERMISSION SERVICE - Permisos Granulares
Agregado: Octubre 10, 2025

AGREGAR ESTAS FUNCIONES AL ARCHIVO permission_service.py EXISTENTE
"""

import json

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
    from app import get_db_connection
    
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
    
    Ejemplo:
    base = {"candidates": {"view_scope": "own", "create": true}}
    override = {"candidates": {"view_scope": "team"}}
    resultado = {"candidates": {"view_scope": "team", "create": true}}
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
        user_id: ID del usuario
        tenant_id: ID del tenant
        permission_path: Ruta del permiso, ej: "candidates.create" o "dashboard.view_financial"
        required_value: Valor esperado (True por defecto)
    
    Returns:
        bool: True si tiene el permiso
    
    Ejemplo:
        has_permission(user_id, tenant_id, "candidates.create")
        has_permission(user_id, tenant_id, "candidates.view_scope", "team")
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
    
    Args:
        resource_type: 'candidates', 'vacancies', 'clients', etc.
    
    Returns:
        str: 'none', 'own', 'team', 'all'
    """
    # Admin siempre ve todo
    if is_admin(user_id, tenant_id):
        return 'all'
    
    perms = get_effective_permissions(user_id, tenant_id)
    
    if resource_type in perms and isinstance(perms[resource_type], dict):
        return perms[resource_type].get('view_scope', 'none')
    
    return 'none'


def can_perform_action(user_id, tenant_id, resource_type, action):
    """
    Verifica si el usuario puede realizar una acción sobre un recurso.
    
    Args:
        resource_type: 'candidates', 'vacancies', 'clients', etc.
        action: 'create', 'edit', 'delete', 'export', etc.
    
    Returns:
        bool or str: True/False o scope ('own', 'team', 'all')
    
    Ejemplo:
        can_perform_action(user_id, tenant_id, 'candidates', 'create')
        can_perform_action(user_id, tenant_id, 'candidates', 'edit_scope')
    """
    # Admin siempre puede
    if is_admin(user_id, tenant_id):
        return True if not action.endswith('_scope') else 'all'
    
    perms = get_effective_permissions(user_id, tenant_id)
    
    if resource_type in perms and isinstance(perms[resource_type], dict):
        value = perms[resource_type].get(action, False)
        return value
    
    return False


# Ejemplo de uso:
"""
# Verificar si puede crear candidatos
if has_permission(user_id, tenant_id, "candidates.create"):
    # Crear candidato...
    pass

# Obtener scope de candidatos
scope = get_permission_scope(user_id, tenant_id, "candidates")
if scope == "all":
    # Ver todos los candidatos
elif scope == "team":
    # Ver candidatos del equipo
elif scope == "own":
    # Ver solo propios

# Verificar acción específica
if can_perform_action(user_id, tenant_id, "dashboard", "view_financial"):
    # Mostrar datos financieros
"""

