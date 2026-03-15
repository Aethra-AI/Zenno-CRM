# -*- coding: utf-8 -*-
import os
import json
import time
import logging
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

# Configurar logger
logger = logging.getLogger(__name__)

# Imports opcionales
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False
# Imports de Flask (opcionales)
try:
    from flask import Flask, jsonify, request, Response, send_file
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    Flask = None
    jsonify = None
    request = None
    Response = None
    send_file = None
    CORS = None
    FLASK_AVAILABLE = False

# Imports de base de datos (opcionales)
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    mysql = None
    MYSQL_AVAILABLE = False

# Imports de configuración (opcionales)
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    load_dotenv = None
    DOTENV_AVAILABLE = False
# ✨ REEMPLAZA la línea 'from datetime import datetime' CON ESTE BLOQUE COMPLETO ✨
from datetime import datetime, date, timedelta
from decimal import Decimal
import io
import re # Importado para la limpieza de números de teléfono

# --- NUEVAS IMPORTACIONES ---
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
from openai import OpenAI
import pytz
from drive_uploader import upload_file_to_drive
import re
import hashlib
from celery_tasks import send_whatsapp_notification_task, calculate_candidate_score
from whatsapp_notification_service import (
    send_application_notification,
    send_interview_notification,
    send_hired_notification,
    send_status_change_notification,
    can_use_whatsapp_conversations
)
# ✨ MÓDULO B5 - Sistema de Permisos y Jerarquía
from permission_service import (
    can_create_resource,
    can_access_resource,
    build_user_filter_condition,
    is_admin,
    get_user_role_name,
    get_accessible_user_ids,
    can_manage_users,
    is_supervisor,
    get_user_permissions,
    get_effective_permissions,
    has_permission,
    get_permission_scope,
    can_perform_action,
    # Helpers por pestañas (Fase 3)
    can_access_tab,
    get_scope_for_tab,
    can_action_on_tab,
    get_ui_flags_for_tab,
    get_redactions_for_tab
)
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request, Response, send_file, send_from_directory, g, url_for, redirect
import jwt
import bcrypt

# Importaciones para OCI Object Storage (opcionales)
try:
    from oci_storage_service import oci_storage_service
    from cv_processing_service import cv_processing_service
    OCI_SERVICES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Servicios OCI no disponibles: {str(e)}")
    OCI_SERVICES_AVAILABLE = False
    oci_storage_service = None
    cv_processing_service = None

# --- WHATSAPP MULTI-TENANT IMPORTS ---
from whatsapp_config_manager import config_manager, get_tenant_whatsapp_config, create_tenant_whatsapp_config, update_tenant_whatsapp_config
from whatsapp_webhook_handler import handle_whatsapp_webhook_get, handle_whatsapp_webhook_post
from whatsapp_business_api_manager import send_whatsapp_message, get_whatsapp_message_status, api_manager
from whatsapp_web_manager import get_tenant_whatsapp_mode, initialize_whatsapp_web_session, send_whatsapp_web_message, get_whatsapp_web_status, web_manager

# --- PUBLIC API SERVICE ---
from public_api_service import public_api_service

# --- DATABASE MIGRATIONS ---
from database_migrations import run_database_migrations

import logging
from logging.handlers import RotatingFileHandler
import traceback
from functools import wraps
import uuid
import re
import secrets
import string
from datetime import datetime, timedelta

# --- CONFIGURACIÓN INICIAL --- 
load_dotenv()
app = Flask(__name__)

app.config['SECRET_KEY'] = 'macarronconquesoysandia151123'

# --- WHATSAPP WEBHOOK HANDLER INICIALIZADO ---
# Se inicializa automáticamente al importar el módulo

# --- CONFIGURACIÓN DE LOGGING ---
if not app.debug:
    # Configurar el handler de archivos rotativos
    file_handler = RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=3)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('CRM Backend startup')

github_pages_url = "https://henmir-hn.github.io/portal-empleo-henmir"

# --- EJECUTAR MIGRACIONES DE BASE DE DATOS ---
# Esto se ejecuta automáticamente al iniciar el servidor
try:
    app.logger.info("🔄 Verificando migraciones de base de datos...")
    db_config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'database': os.getenv('DB_NAME')
    }
    
    if run_database_migrations(db_config):
        app.logger.info("✅ Migraciones de base de datos completadas")
    else:
        app.logger.warning("⚠️  Algunas migraciones fallaron, revisa los logs")
except Exception as e:
    app.logger.error(f"❌ Error ejecutando migraciones: {str(e)}")
    # No detener el servidor, solo registrar el error

# Reemplaza la línea CORS(app) con este bloque
CORS(app, 
     # Aplica esta configuración a todas las rutas que empiecen con /api/ o /public-api/
     resources={r"/*": {"origins": "*"}},
     # Permite explícitamente los métodos que usamos, incluyendo OPTIONS
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     # LA LÍNEA MÁS IMPORTANTE: Permite explícitamente la cabecera de autorización y X-API-Key
     allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-API-Key"],
     # Permite que el navegador envíe credenciales (cookies, tokens)
     supports_credentials=True
)
# OpenAI client will be initialized per request for multi-tenant support
# AGREGA ESTE BLOQUE COMPLETO DESPUÉS DE LA LÍNEA 'openai_client = ...'

from functools import wraps # <<< ASEGÚRATE DE QUE ESTA IMPORTACIÓN ESTÉ ARRIBA CON LAS DEMÁS

# --- CONFIGURACIÓN DE SEGURIDAD PARA LA API DEL BOT ---
INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY')


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Endpoint para autenticar usuarios. Recibe un email y contraseña,
    y si son válidos, devuelve un token JWT.
    
    Parámetros (JSON):
    - email: Correo electrónico del usuario (requerido)
    - password: Contraseña del usuario (requerida)
    
    Respuesta exitosa (200):
    {
        "token": "jwt.token.here",
        "user": {
            "id": 1,
            "nombre": "Nombre Usuario",
            "email": "usuario@ejemplo.com",
            "rol": "admin",
            "permisos": {"ver_dashboard": true, ...}
        }
    }
    
    Errores:
    - 400: Datos faltantes o inválidos
    - 401: Credenciales inválidas
    - 500: Error del servidor
    """
    start_time = datetime.now()
    ip_address = request.remote_addr
    user_agent = request.user_agent.string if request.user_agent else "Desconocido"
    
    app.logger.info("--- INICIANDO PROCESO DE LOGIN ---")
    app.logger.info(f"IP: {ip_address}, User-Agent: {user_agent}")
    
    try:
        # Validar que la solicitud es JSON
        if not request.is_json:
            app.logger.warning("Intento de login sin datos JSON")
            return jsonify({
                'error': 'La solicitud debe ser de tipo application/json'
            }), 400
            
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validaciones básicas
        if not email or not password:
            app.logger.warning("Intento de login sin email o contraseña")
            return jsonify({
                'error': 'Email y contraseña son requeridos',
                'status': 'error',
                'code': 'MISSING_CREDENTIALS'
            }), 400
            
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            app.logger.warning(f"Formato de email inválido: {email}")
            return jsonify({
                'error': 'El formato del correo electrónico no es válido',
                'status': 'error',
                'code': 'INVALID_EMAIL_FORMAT'
            }), 400
            
        app.logger.info(f"Validando credenciales para el email: {email}")
        
        # Obtener conexión a la base de datos
        conn = get_db_connection()
        if not conn:
            app.logger.error("No se pudo conectar a la base de datos")
            return jsonify({
                'error': 'Error en el servidor',
                'status': 'error',
                'code': 'DATABASE_ERROR'
            }), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Obtener el usuario con información del rol y cliente
        cursor.execute("""
            SELECT u.*, r.nombre as rol_nombre, r.permisos, t.nombre_empresa as empresa_nombre,
                   (SELECT COUNT(*) FROM UserSessions 
                    WHERE user_id = u.id AND expira > NOW()) as sessions_count
            FROM Users u 
            LEFT JOIN Roles r ON u.rol_id = r.id
            LEFT JOIN Tenants t ON u.tenant_id = t.id
            WHERE u.email = %s AND u.activo = 1
        """, (email,))
        
        user = cursor.fetchone()
        
        # Registrar intento de login (incluso si falla para auditoría)
        login_attempt = {
            'email': email,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'success': False,
            'details': {}
        }

        if not user:
            app.logger.warning(f"LOGIN FALLIDO: Usuario no encontrado - Email: {email}")
            login_attempt['details'] = {'reason': 'Usuario no encontrado'}
            log_user_activity(
                user_id=None,  # No hay usuario aún
                action='login_failed',
                details=login_attempt,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Pequeña pausa para evitar ataques de fuerza bruta
            time.sleep(1)
            
            return jsonify({
                'error': 'Credenciales inválidas',
                'status': 'error',
                'code': 'INVALID_CREDENTIALS'
            }), 401

        app.logger.info(f"Usuario encontrado. ID: {user['id']}, Rol: {user.get('rol_nombre', 'sin rol')}")
        
        # Verificar si el usuario está bloqueado o inactivo
        if not user.get('activo', False):
            app.logger.warning(f"Intento de login para cuenta inactiva - UserID: {user['id']}")
            login_attempt.update({
                'user_id': user['id'],
                'details': {'reason': 'Cuenta inactiva o bloqueada'}
            })
            log_user_activity(
                user_id=user['id'],
                action='login_blocked',
                details=login_attempt,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return jsonify({
                'error': 'Esta cuenta está inactiva o ha sido bloqueada',
                'status': 'error',
                'code': 'ACCOUNT_INACTIVE'
            }), 403
        
        # Verificar la contraseña
        password_correct = False
        try:
            password_correct = bcrypt.checkpw(
                password.encode('utf-8'), 
                user['password_hash'].encode('utf-8')
            )
        except Exception as e:
            app.logger.error(f"Error al verificar contraseña: {str(e)}")
        
        if not password_correct:
            app.logger.warning(f"LOGIN FALLIDO: Contraseña incorrecta - UserID: {user['id']}")
            
            # Registrar intento fallido
            login_attempt.update({
                'user_id': user['id'],
                'details': {'reason': 'Contraseña incorrecta'}
            })
            log_user_activity(
                user_id=user['id'],
                action='login_failed',
                details=login_attempt,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Pequeña pausa para evitar ataques de fuerza bruta
            time.sleep(1.5)
            
            return jsonify({
                'error': 'Credenciales inválidas',
                'status': 'error',
                'code': 'INVALID_CREDENTIALS'
            }), 401
        
        # Generar token JWT
        token_expiration = datetime.utcnow() + timedelta(hours=8)
        token_data = {
            'user_id': user['id'],
            'email': user['email'],
            'rol': user['rol_nombre'],
            'permisos': json.loads(user['permisos']) if user.get('permisos') else {},
            'tenant_id': user.get('tenant_id'),
            'cliente_id': user.get('id_cliente'),
            'cliente_nombre': user.get('empresa_nombre', ''),
            'exp': token_expiration,
            'jti': str(uuid.uuid4())  # Identificador único del token
        }
        
        token = jwt.encode(token_data, app.config['SECRET_KEY'], algorithm="HS256")
        
        # Registrar la sesión en la base de datos
        try:
            cursor.execute("""
                INSERT INTO UserSessions 
                (user_id, token_id, ip_address, user_agent, expira, creado_en)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (user['id'], token, ip_address, user_agent, token_expiration))
            conn.commit()
        except Exception as e:
            app.logger.error(f"Error al registrar sesión: {str(e)}")
            return jsonify({
                'error': 'Error al registrar sesión',
                'status': 'error',
                'code': 'SESSION_REGISTRATION_ERROR'
            }), 500
        
        # Registrar el login exitoso
        login_attempt.update({
            'user_id': user['id'],
            'success': True
        })
        log_user_activity(
            user_id=user['id'],
            action='login_success',
            details=login_attempt,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        app.logger.info(f"LOGIN EXITOSO - UserID: {user['id']}")
        
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'nombre': user['nombre'],
                'email': user['email'],
                'rol': user['rol_nombre'],
                'tenant_id': user['tenant_id'],
                'cliente_id': user.get('id_cliente'),
                'cliente_nombre': user.get('empresa_nombre', ''),
                'permisos': json.loads(user['permisos']) if user.get('permisos') else {}
            }
        }), 200
    
    except Exception as e:
        app.logger.error(f"Error crítico en el login: {str(e)}")
        return jsonify({
            'error': 'Ocurrió un error en el servidor',
            'status': 'error',
            'code': 'SERVER_ERROR'
        }), 500
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()


def token_required(f):
    """
    Decorador para verificar que un token JWT válido esté presente en las cabeceras
    de la petición.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        app.logger.info(f"Token required - Headers: {dict(request.headers)}")
        token = None
        # El token se espera en el formato 'Bearer <token>'
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
                app.logger.info(f"Token extraído: {token[:20]}...")
            except IndexError:
                app.logger.error("Token con formato incorrecto")
                return jsonify({'message': 'Token con formato incorrecto'}), 401

        if not token:
            app.logger.error("No se encontró token en headers")
            return jsonify({'message': 'Token es requerido'}), 401

        try:
            # Decodifica el token usando la misma clave secreta
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            app.logger.info(f"Token decodificado exitosamente para usuario: {data.get('user_id')}")
            
            # Extraer y almacenar el tenant_id en el contexto global
            tenant_id = data.get('tenant_id')
            if not tenant_id:
                return jsonify({'message': 'Token inválido: falta información de inquilino'}), 401
            
            g.current_tenant_id = tenant_id
            g.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'El token ha expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido'}), 401
        except Exception as e:
            return jsonify({'message': f'Error al procesar el token: {e}'}), 401

        # Si el token es válido, permite que la petición continúe a la ruta original
        return f(*args, **kwargs)
    return decorated


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == INTERNAL_API_KEY:
            return f(*args, **kwargs)
        else:
            # Log de acceso no autorizado
            app.logger.warning(f"Acceso no autorizado al API interno. Clave recibida: {api_key}")
            return jsonify({"error": "Acceso no autorizado"}), 401
    return decorated_function


def public_api_key_required(f):
    """
    Decorador para validar API Keys públicas en endpoints externos.
    Valida la API Key, verifica rate limits y registra el uso.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        import time
        start_time = time.time()
        
        # Obtener API Key del header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            app.logger.warning("Petición sin API Key")
            return jsonify({
                'success': False,
                'error': 'API Key requerida',
                'message': 'Debes incluir el header X-API-Key con tu clave de API'
            }), 401
        
        # Validar API Key
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Error de conexión al servidor'
            }), 500
        
        try:
            is_valid, api_key_data = public_api_service.validate_api_key(conn, api_key)
            
            if not is_valid:
                error_msg = api_key_data.get('error', 'API Key inválida') if api_key_data else 'API Key inválida'
                
                # Registrar intento fallido
                if api_key_data and 'id' in api_key_data:
                    public_api_service.log_api_request(
                        conn=conn,
                        api_key_id=api_key_data['id'],
                        tenant_id=api_key_data.get('tenant_id', 0),
                        endpoint=request.path,
                        metodo=request.method,
                        status_code=401,
                        ip_origen=request.remote_addr,
                        user_agent=request.user_agent.string if request.user_agent else None,
                        error_message=error_msg
                    )
                
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 401
            
            # Verificar rate limit
            rate_limit_ok, requests_remaining = public_api_service.check_rate_limit(
                conn=conn,
                api_key_id=api_key_data['id'],
                rate_limit_per_minute=api_key_data['rate_limit_per_minute']
            )
            
            if not rate_limit_ok:
                public_api_service.log_api_request(
                    conn=conn,
                    api_key_id=api_key_data['id'],
                    tenant_id=api_key_data['tenant_id'],
                    endpoint=request.path,
                    metodo=request.method,
                    status_code=429,
                    ip_origen=request.remote_addr,
                    user_agent=request.user_agent.string if request.user_agent else None,
                    error_message='Rate limit excedido'
                )
                
                return jsonify({
                    'success': False,
                    'error': 'Rate limit excedido',
                    'message': f'Has excedido el límite de {api_key_data["rate_limit_per_minute"]} peticiones por minuto'
                }), 429
            
            # Almacenar datos de la API Key en el contexto
            g.api_key_data = api_key_data
            g.tenant_id = api_key_data['tenant_id']
            
            # Ejecutar la función
            response = f(*args, **kwargs)
            
            # Calcular tiempo de respuesta
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Registrar uso exitoso
            status_code = response[1] if isinstance(response, tuple) else 200
            
            public_api_service.log_api_request(
                conn=conn,
                api_key_id=api_key_data['id'],
                tenant_id=api_key_data['tenant_id'],
                endpoint=request.path,
                metodo=request.method,
                status_code=status_code,
                ip_origen=request.remote_addr,
                user_agent=request.user_agent.string if request.user_agent else None,
                query_params=dict(request.args),
                response_time_ms=response_time_ms
            )
            
            return response
            
        except Exception as e:
            app.logger.error(f"Error en validación de API Key pública: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Error interno del servidor'
            }), 500
        finally:
            if conn:
                conn.close()
    
    return decorated


# --- FUNCIÓN DE CONEXIÓN A LA BD ---
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'), port=int(os.getenv('DB_PORT')),
            database=os.getenv('DB_NAME')
        )
    except mysql.connector.Error as err:
        app.logger.error(f"Error de conexión a la base de datos: {err}")
        return None

# --- ✨ FUNCIONES AUXILIARES PARA MULTI-TENANCY ✨ ---
def get_current_tenant_id():
    """
    Obtiene el tenant_id del contexto actual de la petición.
    Debe usarse dentro de rutas protegidas con @token_required.
    """
    return getattr(g, 'current_tenant_id', None)

def add_tenant_filter(base_query, table_alias='', tenant_column='tenant_id'):
    """
    Agrega filtro de tenant a una consulta SQL.
    
    Args:
        base_query (str): La consulta SQL base
        table_alias (str): Alias de la tabla principal (opcional)
        tenant_column (str): Nombre de la columna que contiene el tenant_id
    
    Returns:
        tuple: (query_with_filter, tenant_id)
    """
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise ValueError("No se encontró tenant_id en el contexto de la petición")
    
    # Agregar el prefijo de tabla si se proporciona
    column_ref = f"{table_alias}.{tenant_column}" if table_alias else tenant_column
    
    # Agregar filtro WHERE o AND según corresponda
    if "WHERE" in base_query.upper():
        filtered_query = f"{base_query} AND {column_ref} = %s"
    else:
        filtered_query = f"{base_query} WHERE {column_ref} = %s"
    
    return filtered_query, tenant_id

def log_activity(activity_type, description, user_id=None, tenant_id=None, ip_address=None, user_agent=None):
    """
    Registra una actividad en UserActivityLog
    
    Args:
        activity_type (str): Tipo de actividad (ej: 'postulacion_creada', 'candidato_creado', etc.)
        description (str or dict): Descripción de la actividad (puede ser string o dict que se convertirá a JSON)
        user_id (int): ID del usuario que realizó la acción (opcional, se obtiene del contexto)
        tenant_id (int): ID del tenant (opcional, se obtiene del contexto)
        ip_address (str): IP del usuario (opcional, se obtiene del request)
        user_agent (str): User agent del navegador (opcional, se obtiene del request)
    
    Returns:
        bool: True si se registró correctamente, False en caso contrario
    """
    conn = None
    try:
        # Obtener valores del contexto si no se proporcionaron
        if user_id is None:
            user_data = getattr(g, 'current_user', None)
            user_id = user_data.get('user_id') if user_data else None
        
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
        
        if ip_address is None:
            ip_address = request.remote_addr if request else None
        
        if user_agent is None:
            user_agent = request.headers.get('User-Agent', 'Unknown') if request else 'Unknown'
        
        # Convertir description a JSON si es un diccionario
        if isinstance(description, dict):
            description = json.dumps(description, ensure_ascii=False)
        
        # Validar que tenemos los datos mínimos necesarios
        if not user_id or not tenant_id:
            app.logger.warning(f"No se pudo registrar actividad: user_id={user_id}, tenant_id={tenant_id}")
            return False
        
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO UserActivityLog 
            (user_id, tenant_id, activity_type, description, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, tenant_id, activity_type, description, ip_address, user_agent))
        
        conn.commit()
        app.logger.info(f"Actividad registrada: {activity_type} - Usuario: {user_id} - Tenant: {tenant_id}")
        return True
        
    except Exception as e:
        app.logger.error(f"Error al registrar actividad: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()

def create_notification(user_id, tenant_id, tipo, titulo, mensaje, prioridad='media', metadata=None):
    """
    Crea una notificación para un usuario
    
    Args:
        user_id (int): ID del usuario destinatario
        tenant_id (int): ID del tenant
        tipo (str): Tipo de notificación
        titulo (str): Título de la notificación
        mensaje (str): Mensaje de la notificación
        prioridad (str): Prioridad (alta/media/baja)
        metadata (dict): Datos adicionales en formato dict
    
    Returns:
        int: ID de la notificación creada o None si hubo error
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        # Convertir metadata a JSON si se proporciona
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        
        cursor.execute("""
            INSERT INTO notifications 
            (user_id, tenant_id, tipo, titulo, mensaje, prioridad, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, tenant_id, tipo, titulo, mensaje, prioridad, metadata_json))
        
        conn.commit()
        notification_id = cursor.lastrowid
        
        app.logger.info(f"Notificación creada: {notification_id} - Usuario: {user_id} - Tipo: {tipo}")
        return notification_id
        
    except Exception as e:
        app.logger.error(f"Error al crear notificación: {str(e)}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


# --- ENDPOINTS DE AUTENTICACIÓN ADICIONALES ---

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout():
    """
    Endpoint para cerrar sesión del usuario
    """
    try:
        # El token ya fue validado por el decorador @token_required
        # Solo necesitamos responder con éxito
        return jsonify({
            'message': 'Sesión cerrada exitosamente',
            'status': 'success'
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error en logout: {str(e)}")
        return jsonify({
            'error': 'Error al cerrar sesión',
            'status': 'error'
        }), 500


@app.route('/api/users/me', methods=['GET'])
@token_required
def get_current_user():
    """
    Endpoint para obtener información del usuario actual
    """
    conn = get_db_connection()
    if not conn: 
        return jsonify({"error": "Error de conexión"}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Obtener datos del token (ya validado)
        user_data = g.current_user
        user_id = user_data.get('user_id')
        
        # Obtener información actualizada del usuario
        cursor.execute("""
            SELECT u.*, r.nombre as rol_nombre, r.permisos, t.nombre_empresa as empresa_nombre
            FROM Users u 
            LEFT JOIN Roles r ON u.rol_id = r.id
            LEFT JOIN Tenants t ON u.tenant_id = t.id
            WHERE u.id = %s AND u.activo = 1
        """, (user_id,))
        
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'nombre': user['nombre'],
            'rol': user['rol_nombre'],
            'cliente': user.get('empresa_nombre', ''),
            'permisos': json.loads(user['permisos']) if user.get('permisos') else {}
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error obteniendo usuario actual: {str(e)}")
        return jsonify({"error": "Error al obtener información del usuario"}), 500
    finally:
        cursor.close()
        conn.close()


# --- ✨ NUEVO BLOQUE DE FUNCIONES AUXILIARES PARA NOTIFICACIONES ✨ ---

def get_honduras_time():
    """Devuelve la fecha y hora actual en la zona horaria de Honduras."""
    hn_timezone = pytz.timezone('America/Tegucigalpa')
    return datetime.now(hn_timezone)

def _send_task_to_bridge(task_data):
    """
    Función interna para enviar una tarea de notificación al servidor bridge.js.
    No detiene el flujo principal si bridge.js no está disponible.
    """
    try:
        bridge_url = os.getenv('BRIDGE_API_URL', 'https://34.63.21.5.sslip.io/bridge') + '/api/internal/queue_whatsapp_message'
        # Usamos un timeout corto para no bloquear la respuesta al usuario del CRM
        response = requests.post(bridge_url, json=task_data, timeout=5)
        if response.status_code == 200:
            app.logger.info(f"Tarea enviada exitosamente a bridge.js: {task_data.get('task_type')}")
            return True
        else:
            app.logger.error(f"Error al enviar tarea a bridge.js. Status: {response.status_code}, Body: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        app.logger.error(f"No se pudo conectar con bridge.js para enviar la tarea. Error: {e}")
        return False

# --- FIN DEL NUEVO BLOQUE ---

def generate_secure_filename(doc_type, user_id, original_filename, sequence=None):
    """
    Genera un nombre de archivo completamente seguro y único.
    
    Args:
        doc_type: Tipo de documento ("CV", "ID", etc.)
        user_id: Identificador del usuario (cédula limpia)
        original_filename: Nombre original del archivo
        sequence: Número de secuencia para múltiples archivos (opcional)
    
    Returns:
        str: Nombre de archivo seguro y único
    """
    # Sanitizar el nombre original del archivo
    safe_original = re.sub(r'[^a-zA-Z0-9._-]', '_', original_filename)
    safe_original = re.sub(r'_{2,}', '_', safe_original)  # Reducir múltiples underscores
    
    # Obtener extensión de forma segura
    if '.' in safe_original:
        name_part, extension = safe_original.rsplit('.', 1)
        extension = extension.lower()[:10]  # Limitar longitud de extensión
    else:
        name_part = safe_original
        extension = 'bin'
    
    # Crear timestamp único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Incluir microsegundos
    
    # Crear hash único basado en contenido y timestamp
    hash_input = f"{doc_type}_{user_id}_{timestamp}_{name_part}"
    file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    # Construir nombre final
    components = [doc_type, user_id, timestamp, file_hash]
    if sequence:
        components.append(f"seq{sequence}")
    
    final_name = "_".join(components) + f".{extension}"
    
    # Asegurar que no exceda límites del sistema de archivos
    if len(final_name) > 255:
        final_name = final_name[:250] + f".{extension}"
    
    return final_name

def clean_phone_number(phone_str):
    """Limpia y estandariza los números de teléfono para Honduras."""
    if not phone_str:
        return None
    # Eliminar todos los caracteres que no sean dígitos
    digits = re.sub(r'\D', '', str(phone_str))
    # Si el número ya empieza con 504 y tiene 11 dígitos, es correcto
    if digits.startswith('504') and len(digits) == 11:
        return digits
    # Si tiene 8 dígitos, le añadimos el código de país
    if len(digits) == 8:
        return '504' + digits
    # En otros casos, devolvemos el número limpio, pero podría ser inválido
    return digits

# --- RUTA DE PRUEBA ---
@app.route('/')
def index():
    return "Servidor del CRM Henmir está en línea. Versión Definitiva con Asistente IA."

# ===============================================================
# SECCIÓN 1: ASISTENTE DE IA (OpenAI)
# ===============================================================

# AÑADE ESTA NUEVA FUNCIÓN AYUDANTE al inicio de la SECCIÓN 1 en app.py

def _get_candidate_id(conn, candidate_id: int = None, identity_number: str = None) -> int:
    """Función interna para obtener el id_afiliado. Prioriza el candidate_id si está presente."""
    if candidate_id:
        return candidate_id
    
    if identity_number:
        cursor = conn.cursor(dictionary=True)
        clean_identity = str(identity_number).replace('-', '').strip()
        tenant_id = get_current_tenant_id()
        query = "SELECT id_afiliado FROM Afiliados WHERE identidad = %s LIMIT 1"
        cursor.execute(query, (clean_identity,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return result['id_afiliado']
            
    return None

# --- Funciones que el Asistente de IA puede llamar ---
def get_candidates_by_ids(ids: list):
    """Obtiene información de contacto de candidatos por sus IDs."""
    conn = get_db_connection()
    if not conn: return json.dumps({"error": "DB connection failed"})
    cursor = conn.cursor(dictionary=True)
    try:
        safe_ids = [int(i) for i in ids]
        if not safe_ids: return json.dumps([])
        tenant_id = get_current_tenant_id()
        placeholders = ','.join(['%s'] * len(safe_ids))
        query = f"SELECT id_afiliado, nombre_completo, telefono FROM Afiliados WHERE id_afiliado IN ({placeholders})"
        cursor.execute(query, tuple(safe_ids))
        results = cursor.fetchall()
        for r in results:
            r['telefono'] = clean_phone_number(r.get('telefono'))
        return json.dumps(results)
    finally:
        cursor.close()
        conn.close()

def get_candidates_by_tag(tag_name: str):
    """Obtiene información de contacto de candidatos que tienen una etiqueta específica."""
    conn = get_db_connection()
    if not conn: return json.dumps({"error": "DB connection failed"})
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        query = """
            SELECT a.id_afiliado, a.nombre_completo, a.telefono 
            FROM Afiliados a 
            JOIN Afiliado_Tags at ON a.id_afiliado = at.id_afiliado 
            JOIN Tags t ON at.id_tag = t.id_tag 
            WHERE t.nombre_tag = %s AND a.id_cliente = %s AND t.id_cliente = %s
        """
        cursor.execute(query, (tag_name, tenant_id, tenant_id))
        results = cursor.fetchall()
        for r in results:
            r['telefono'] = clean_phone_number(r.get('telefono'))
        return json.dumps(results)
    finally:
        cursor.close()
        conn.close()

def get_vacancy_details(vacancy_name: str):
    """Obtiene detalles de una vacante por su nombre."""
    conn = get_db_connection()
    if not conn: return json.dumps({"error": "DB connection failed"})
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT cargo_solicitado, empresa FROM Vacantes v JOIN Clientes c ON v.id_cliente = c.id_cliente WHERE v.cargo_solicitado LIKE %s LIMIT 1"
        cursor.execute(query, (f"%{vacancy_name}%",))
        result = cursor.fetchone()
        return json.dumps(result)
    finally:
        cursor.close()
        conn.close()
        
        
def get_candidate_id_by_identity(identity_number: str):
    """Obtiene el ID numérico de un afiliado a partir de su número de identidad."""
    conn = get_db_connection()
    if not conn: return json.dumps({"error": "DB connection failed"})
    cursor = conn.cursor(dictionary=True)
    try:
        clean_identity = str(identity_number).replace('-', '').strip()
        tenant_id = get_current_tenant_id()
        query = "SELECT id_afiliado FROM Afiliados WHERE identidad = %s LIMIT 1"
        cursor.execute(query, (clean_identity,))
        result = cursor.fetchone()
        return json.dumps(result)
    finally:
        cursor.close()
        conn.close()
        
    

def postulate_candidate_to_vacancy(vacancy_id: int, candidate_id: int = None, identity_number: str = None, comments: str = ""):
    """Postula un candidato a una vacante usando su ID de candidato o su número de identidad."""
    conn = get_db_connection()
    if not conn: return json.dumps({"error": "DB connection failed"})
    
    # Usamos la función ayudante para encontrar el ID correcto
    final_candidate_id = _get_candidate_id(conn, candidate_id, identity_number)
    
    if not final_candidate_id:
        return json.dumps({"success": False, "error": f"No se pudo encontrar al candidato con los datos proporcionados."})

    cursor = conn.cursor()
    try:
        # Verificar si la postulación ya existe
        cursor.execute("SELECT id_postulacion FROM Postulaciones WHERE id_afiliado = %s AND id_vacante = %s", (final_candidate_id, vacancy_id))
        if cursor.fetchone():
            return json.dumps({"success": False, "message": f"El candidato (ID: {final_candidate_id}) ya ha postulado a esta vacante."})
        
        # Insertar la nueva postulación
        sql = "INSERT INTO Postulaciones (id_afiliado, id_vacante, fecha_aplicacion, estado, comentarios) VALUES (%s, %s, NOW(), 'Recibida', %s)"
        cursor.execute(sql, (final_candidate_id, vacancy_id, comments))
        conn.commit()
        return json.dumps({"success": True, "message": f"Postulación del candidato (ID: {final_candidate_id}) registrada correctamente."})
    except Exception as e:
        conn.rollback()
        return json.dumps({"success": False, "error": str(e)})
    finally:
        cursor.close()
        conn.close()        
        
                

# ===============================================================
# 🤖 NUEVO BOT MULTI-TENANT CON OPENAI
# ===============================================================

@app.route('/api/assistant/command', methods=['POST'])
@token_required
def assistant_command():
    """Nuevo endpoint del bot que respeta la arquitectura multi-tenant"""
    data = request.get_json()
    user_prompt = data.get('prompt')
    history = data.get('history', [])
    
    if not user_prompt:
        return jsonify({"error": "Prompt es requerido"}), 400

    try:
        # Obtener información del tenant actual
        current_user = g.current_user
        
        # DEBUG: Verificar tipo de current_user
        app.logger.info(f"DEBUG - Tipo de current_user: {type(current_user)}")
        app.logger.info(f"DEBUG - Contenido de current_user: {current_user}")
        
        # Si current_user es una tupla, extraer el diccionario
        if isinstance(current_user, tuple):
            app.logger.warning("current_user es una tupla, extrayendo primer elemento")
            current_user = current_user[0] if len(current_user) > 0 else {}
        
        tenant_id = get_current_tenant_id()
        user_role = current_user.get('rol', '') if isinstance(current_user, dict) else ''
        
        # Inicializar cliente OpenAI por request (multi-tenant)
        openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Obtener empresa_nombre de forma segura
        empresa_nombre = current_user.get('empresa_nombre', 'la organización') if isinstance(current_user, dict) else 'la organización'
        
        # Construir mensajes con contexto del tenant
        messages = [
                   {
                       "role": "system",
                       "content": f"""Eres un asistente de reclutamiento experto para {empresa_nombre}.
                       Tu personalidad es proactiva, eficiente y directa.

                       CONTEXTO ACTUAL:
                       - Organización: {empresa_nombre}
                       - Tu rol: {user_role}
                       - Tenant ID: {tenant_id}

                       FUNCIONALIDADES DISPONIBLES:
                       🔍 BÚSQUEDA DE CANDIDATOS:
                       - Por ID: "busca el candidato con id 1" → usar search_candidates con candidate_id
                       - Por nombre: "busca Juan Pérez" → usar search_candidates con term
                       - Por experiencia: "busca desarrolladores" → usar search_candidates con experience
                       - Por ciudad: "busca en Madrid" → usar search_candidates con city
                       
                       📋 GESTIÓN DE VACANTES:
                       - Ver vacantes: "muestra las vacantes disponibles"
                       - Buscar por ciudad: "vacantes en Barcelona"
                       
                       📊 REPORTES:
                       - Dashboard: "muestra estadísticas del dashboard"
                       
                       📱 WHATSAPP:
                       - Campañas: "envía mensaje a candidato 1"
                       
                       REGLAS CRÍTICAS:
                       1. Aislamiento de datos: Solo puedes acceder a datos del tenant {tenant_id}
                       2. Uso de Herramientas: Para cualquier acción que implique buscar, postular, agendar o actualizar datos, DEBES usar una herramienta
                       3. Contexto: Presta atención al historial para entender órdenes de seguimiento
                       4. Clarificación: Si una orden es ambigua, pregunta para clarificar antes de usar una herramienta
                       5. Identificadores: Prioriza IDs numéricos si están disponibles en el historial
                       6. Búsqueda por ID: Cuando el usuario mencione "id" seguido de un número, usa candidate_id
                       """
                   }
               ]
        
        # Agregar historial
        for item in history:
            if item.get('user'): 
                messages.append({"role": "user", "content": item.get('user')})
            if item.get('assistant'): 
                messages.append({"role": "assistant", "content": item.get('assistant')})
        
        messages.append({"role": "user", "content": user_prompt})

        # Herramientas del bot multi-tenant
        tools = [
            {
                "type": "function", 
                "function": {
                    "name": "search_candidates_multi_tenant", 
                    "description": "Busca candidatos del tenant actual",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "term": {"type": "string", "description": "Término de búsqueda"},
                            "tags": {"type": "string", "description": "Tags a buscar"},
                            "experience": {"type": "string", "description": "Años de experiencia o texto de experiencia"},
                            "city": {"type": "string", "description": "Ciudad"},
                            "recency_days": {"type": "integer", "description": "Días desde registro"},
                            "candidate_id": {"type": "integer", "description": "ID específico del candidato a buscar"}
                        }, 
                        "required": []
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "get_vacancies_multi_tenant", 
                    "description": "Obtiene vacantes activas del tenant actual",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "city": {"type": "string", "description": "Filtrar por ciudad"},
                            "keyword": {"type": "string", "description": "Palabra clave en cargo o requisitos"}
                        }, 
                        "required": []
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "postulate_candidate_multi_tenant", 
                    "description": "Postula un candidato del tenant actual a una vacante",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "vacancy_id": {"type": "integer", "description": "ID de la vacante"},
                            "candidate_id": {"type": "integer", "description": "ID del candidato"},
                            "identity_number": {"type": "string", "description": "Número de identidad del candidato"},
                            "comments": {"type": "string", "description": "Comentarios adicionales"}
                        }, 
                        "required": ["vacancy_id"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "update_application_status_multi_tenant", 
                    "description": "Actualiza el estado de una postulación del tenant actual",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "postulation_id": {"type": "integer", "description": "ID de la postulación"},
                            "new_status": {"type": "string", "description": "Nuevo estado"}
                        }, 
                        "required": ["postulation_id", "new_status"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "get_dashboard_stats_multi_tenant", 
                    "description": "Obtiene estadísticas del dashboard del tenant actual",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "report_type": {"type": "string", "description": "Tipo de reporte: 'kpi', 'activity', 'metrics'"}
                        }, 
                        "required": []
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "create_whatsapp_campaign_multi_tenant", 
                    "description": "Crea campañas de WhatsApp inteligentes para candidatos del tenant actual",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "message_body": {"type": "string", "description": "Mensaje personalizado. Usa [nombre] para reemplazo automático"},
                            "candidate_ids": {"type": "string", "description": "IDs de candidatos separados por comas"},
                            "vacancy_id": {"type": "integer", "description": "ID de vacante para contactar candidatos postulados"},
                            "template_type": {"type": "string", "description": "Tipo: 'vacancy_invitation', 'interview_reminder', 'status_update', 'custom'"}
                        }, 
                        "required": []
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "register_payment_multi_tenant", 
                    "description": "Registra pagos asociados a candidatos contratados del tenant actual",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "hired_candidate_id": {"type": "integer", "description": "ID del candidato contratado"},
                            "candidate_id": {"type": "integer", "description": "ID del candidato (alternativa a hired_candidate_id)"},
                            "amount": {"type": "number", "description": "Monto del pago"},
                            "payment_type": {"type": "string", "description": "Tipo de pago: 'commission', 'bonus', 'fee'"},
                            "description": {"type": "string", "description": "Descripción del pago"}
                        }, 
                        "required": ["amount"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "generate_predictive_analytics", 
                    "description": "Genera análisis predictivo avanzado del tenant actual",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "analysis_type": {"type": "string", "description": "Tipo: 'hiring_probability', 'attrition_risk', 'salary_benchmark'"},
                            "candidate_id": {"type": "integer", "description": "ID del candidato"},
                            "vacancy_id": {"type": "integer", "description": "ID de la vacante"}
                        }, 
                        "required": ["analysis_type"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "export_data_multi_tenant", 
                    "description": "Exporta datos filtrados a Excel o CSV para el tenant actual",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "export_type": {"type": "string", "description": "Tipo: 'candidates', 'vacancies', 'reports'"},
                            "format_type": {"type": "string", "description": "Formato: 'excel', 'csv', 'json'"},
                            "city": {"type": "string", "description": "Filtrar por ciudad"},
                            "date_from": {"type": "string", "description": "Fecha desde (YYYY-MM-DD)"}
                        }, 
                        "required": ["export_type"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "bulk_operations_multi_tenant", 
                    "description": "Realiza operaciones masivas (postular, actualizar estados) en el tenant actual",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "operation_type": {"type": "string", "description": "Tipo: 'bulk_postulate', 'bulk_status_update'"},
                            "target_ids": {"type": "array", "items": {"type": "integer"}, "description": "Lista de IDs de candidatos o postulaciones"},
                            "vacancy_id": {"type": "integer", "description": "ID de vacante para postulaciones masivas"},
                            "new_status": {"type": "string", "description": "Nuevo estado para actualización masiva"}
                        }, 
                        "required": ["operation_type", "target_ids"]
                    }
                }
            }
        ]

        # Llamada a OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # Procesar llamadas a herramientas si existen
        if response_message.tool_calls:
            available_functions = {
                "search_candidates_multi_tenant": search_candidates_multi_tenant,
                "get_vacancies_multi_tenant": get_vacancies_multi_tenant,
                "postulate_candidate_multi_tenant": postulate_candidate_multi_tenant,
                "update_application_status_multi_tenant": update_application_status_multi_tenant,
                "get_dashboard_stats_multi_tenant": get_dashboard_stats_multi_tenant,
                "create_whatsapp_campaign_multi_tenant": create_whatsapp_campaign_multi_tenant,
                "register_payment_multi_tenant": register_payment_multi_tenant,
                "generate_predictive_analytics": generate_predictive_analytics,
                "export_data_multi_tenant": export_data_multi_tenant,
                "bulk_operations_multi_tenant": bulk_operations_multi_tenant
            }
            
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                
                app.logger.info(f"🤖 Ejecutando herramienta multi-tenant: {function_name} para tenant {tenant_id}")
                
                # Inyectar tenant_id en los argumentos
                function_args['tenant_id'] = tenant_id
                
                function_response = function_to_call(**function_args)
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
            
            # Segunda llamada para generar respuesta final
            second_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )
            return jsonify({"data": second_response.choices[0].message.content})
        
        return jsonify({"data": response_message.content})

    except Exception as e:
        app.logger.error(f"Error en assistant_command multi-tenant: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# --- Funciones de Herramientas Multi-Tenant (Implementación) ---

def search_candidates_multi_tenant(tenant_id: int, term: str = None, tags: str = None, 
                                 experience: str = None, city: str = None, 
                                 recency_days: int = None, candidate_id: int = None):
    """
    Búsqueda avanzada de candidatos filtrando estrictamente por tenant_id
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Si se proporciona un candidate_id, priorizar esa búsqueda directa
        if candidate_id:
            query = """
                SELECT id_afiliado, nombre_completo, email, telefono, experiencia, ciudad, estado, creado_en
                FROM Afiliados 
                WHERE id_afiliado = %s AND tenant_id = %s
                LIMIT 1
            """
            cursor.execute(query, (candidate_id, tenant_id))
            result = cursor.fetchone()
            if result:
                # Convertir fechas para JSON
                if result.get('creado_en'):
                    result['creado_en'] = result['creado_en'].isoformat()
                return json.dumps([result])
            return json.dumps([])

        # Búsqueda general con filtros
        base_query = """
            SELECT id_afiliado, nombre_completo, email, telefono, experiencia, ciudad, estado, creado_en
            FROM Afiliados 
            WHERE tenant_id = %s
        """
        params = [tenant_id]
        
        if term:
            base_query += " AND (nombre_completo LIKE %s OR email LIKE %s)"
            params.extend([f"%{term}%", f"%{term}%"])
        
        if city:
            base_query += " AND ciudad LIKE %s"
            params.append(f"%{city}%")
            
        if experience:
            base_query += " AND experiencia LIKE %s"
            params.append(f"%{experience}%")
            
        if recency_days:
            base_query += " AND creado_en >= DATE_SUB(NOW(), INTERVAL %s DAY)"
            params.append(recency_days)
            
        base_query += " LIMIT 20"
        
        cursor.execute(base_query, params)
        results = cursor.fetchall()
        
        # Convertir fechas para JSON
        for r in results:
            if r.get('creado_en'):
                r['creado_en'] = r['creado_en'].isoformat()
                
        return json.dumps(results)
    except Exception as e:
        app.logger.error(f"Error en search_candidates_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

def get_vacancies_multi_tenant(tenant_id: int, city: str = None, keyword: str = None):
    """
    Obtiene vacantes filtrando estrictamente por tenant_id
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT v.id_vacante, v.cargo_solicitado, v.requisitos, v.ciudad, v.salario, c.empresa
            FROM Vacantes v
            JOIN Clientes c ON v.id_cliente = c.id_cliente
            WHERE v.tenant_id = %s AND v.estado = 'Abierta'
        """
        params = [tenant_id]
        
        if city:
            query += " AND v.ciudad LIKE %s"
            params.append(f"%{city}%")
            
        if keyword:
            query += " AND (v.cargo_solicitado LIKE %s OR v.requisitos LIKE %s)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
            
        cursor.execute(query, params)
        results = cursor.fetchall()
        return json.dumps(results)
    except Exception as e:
        app.logger.error(f"Error en get_vacancies_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

def postulate_candidate_multi_tenant(tenant_id: int, vacancy_id: int, 
                                   candidate_id: int = None, identity_number: str = None, 
                                   comments: str = ""):
    """
    Postula un candidato verificando que ambos pertenezcan al mismo tenant_id
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Verificar que la vacante pertenece al tenant
        cursor.execute("SELECT id_vacante FROM Vacantes WHERE id_vacante = %s AND tenant_id = %s", (vacancy_id, tenant_id))
        if not cursor.fetchone():
            return json.dumps({"success": False, "error": "Vacante no encontrada o no pertenece a su organización"})
            
        # 2. Encontrar el candidato y verificar su tenant
        final_candidate_id = None
        if candidate_id:
            cursor.execute("SELECT id_afiliado FROM Afiliados WHERE id_afiliado = %s AND tenant_id = %s", (candidate_id, tenant_id))
            res = cursor.fetchone()
            if res: final_candidate_id = res['id_afiliado']
        elif identity_number:
            clean_identity = str(identity_number).replace('-', '').strip()
            cursor.execute("SELECT id_afiliado FROM Afiliados WHERE identidad = %s AND tenant_id = %s", (clean_identity, tenant_id))
            res = cursor.fetchone()
            if res: final_candidate_id = res['id_afiliado']
            
        if not final_candidate_id:
            return json.dumps({"success": False, "error": "Candidato no encontrado en su organización"})
            
        # 3. Verificar si ya está postulado
        cursor.execute("SELECT id_postulacion FROM Postulaciones WHERE id_afiliado = %s AND id_vacante = %s", (final_candidate_id, vacancy_id))
        if cursor.fetchone():
            return json.dumps({"success": False, "message": "El candidato ya está postulado a esta vacante"})
            
        # 4. Registrar postulación
        cursor.execute("""
            INSERT INTO Postulaciones (id_afiliado, id_vacante, fecha_aplicacion, estado, comentarios, tenant_id)
            VALUES (%s, %s, NOW(), 'Recibida', %s, %s)
        """, (final_candidate_id, vacancy_id, comments, tenant_id))
        conn.commit()
        
        return json.dumps({"success": True, "message": f"Candidato (ID: {final_candidate_id}) postulado exitosamente a la vacante {vacancy_id}"})
        
    except Exception as e:
        conn.rollback()
        return json.dumps({"success": False, "error": str(e)})
    finally:
        cursor.close()
        conn.close()

def update_application_status_multi_tenant(tenant_id: int, postulation_id: int, new_status: str):
    """
    Actualiza el estado de una postulación verificando el tenant_id
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Verificar pertenencia de la postulación al tenant vía join con Vacantes
        cursor.execute("""
            SELECT p.id_postulacion 
            FROM Postulaciones p
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE p.id_postulacion = %s AND v.tenant_id = %s
        """, (postulation_id, tenant_id))
        
        if not cursor.fetchone():
            return json.dumps({"success": False, "error": "Postulación no encontrada o acceso denegado"})
            
        # Actualizar estado
        cursor.execute("UPDATE Postulaciones SET estado = %s WHERE id_postulacion = %s", (new_status, postulation_id))
        conn.commit()
        
        return json.dumps({"success": True, "message": f"Estado de postulación {postulation_id} actualizado a '{new_status}'"})
        
    except Exception as e:
        conn.rollback()
        return json.dumps({"success": False, "error": str(e)})
    finally:
        cursor.close()
        conn.close()

def get_dashboard_stats_multi_tenant(tenant_id: int, report_type: str = "kpi"):
    """
    Obtiene estadísticas agregadas del tenant actual
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        if report_type == "kpi":
            # KPIs básicos
            cursor.execute("SELECT COUNT(*) as total FROM Afiliados WHERE tenant_id = %s", (tenant_id,))
            total_candidatos = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM Vacantes WHERE tenant_id = %s AND estado = 'Abierta'", (tenant_id,))
            vacantes_abiertas = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM Postulaciones p
                JOIN Vacantes v ON p.id_vacante = v.id_vacante
                WHERE v.tenant_id = %s AND p.fecha_aplicacion >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """, (tenant_id,))
            postulaciones_mes = cursor.fetchone()['total']
            
            return json.dumps({
                "total_candidatos": total_candidatos,
                "vacantes_abiertas": vacantes_abiertas,
                "postulaciones_ultimos_30_dias": postulaciones_mes,
                "periodo": "Últimos 30 días"
            })
        
        elif report_type == "activity":
            # Actividad reciente
            cursor.execute("""
                SELECT p.fecha_aplicacion, a.nombre_completo, v.cargo_solicitado, p.estado
                FROM Postulaciones p
                JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
                JOIN Vacantes v ON p.id_vacante = v.id_vacante
                WHERE v.tenant_id = %s
                ORDER BY p.fecha_aplicacion DESC
                LIMIT 10
            """, (tenant_id,))
            activity = cursor.fetchall()
            for r in activity:
                r['fecha_aplicacion'] = r['fecha_aplicacion'].isoformat()
            return json.dumps(activity)
            
        return json.dumps({"error": f"Tipo de reporte '{report_type}' no soportado"})
        
    except Exception as e:
        app.logger.error(f"Error en get_dashboard_stats_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

def create_whatsapp_campaign_multi_tenant(tenant_id: int, message_body: str = None, 
                                        candidate_ids: str = None, vacancy_id: int = None, 
                                        template_type: str = "custom"):
    """
    Crea una campaña de WhatsApp filtrando por tenant_id
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        final_candidates = []
        
        # Caso 1: Por IDs específicos
        if candidate_ids:
            ids = [int(i.strip()) for i in candidate_ids.split(',')]
            placeholders = ','.join(['%s'] * len(ids))
            query = f"SELECT id_afiliado, nombre_completo, telefono FROM Afiliados WHERE tenant_id = %s AND id_afiliado IN ({placeholders})"
            cursor.execute(query, [tenant_id] + ids)
            final_candidates = cursor.fetchall()
            
        # Caso 2: Por Vacante (contactar a todos los postulados)
        elif vacancy_id:
            cursor.execute("""
                SELECT a.id_afiliado, a.nombre_completo, a.telefono
                FROM Afiliados a
                JOIN Postulaciones p ON a.id_afiliado = p.id_afiliado
                JOIN Vacantes v ON p.id_vacante = v.id_vacante
                WHERE v.id_vacante = %s AND v.tenant_id = %s
            """, (vacancy_id, tenant_id))
            final_candidates = cursor.fetchall()
            
        if not final_candidates:
            return json.dumps({"success": False, "message": "No se encontraron candidatos para la campaña"})

        # Limpiar teléfonos
        for c in final_candidates:
            c['telefono_limpio'] = clean_phone_number(c['telefono'])
            
        # Registrar la campaña en la base de datos (simulación o integración con bridge.js)
        # Por ahora devolvemos el resumen para que el bot confirme
        return json.dumps({
            "success": True,
            "total_candidates": len(final_candidates),
            "candidates": final_candidates,
            "message_preview": message_body or f"Hola [nombre], te contactamos de ESC por una vacante.",
            "template_type": template_type,
            "tenant_id": tenant_id
        })
        
    except Exception as e:
        app.logger.error(f"Error en create_whatsapp_campaign_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

def register_payment_multi_tenant(tenant_id: int, amount: float, hired_candidate_id: int = None, 
                                candidate_id: int = None, payment_type: str = "commission", 
                                description: str = ""):
    """
    Registra un pago financiero asociado a un candidato del tenant actual
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        target_id = hired_candidate_id or candidate_id
        if not target_id:
            return json.dumps({"error": "Se requiere ID de candidato contratado o ID de candidato"})
            
        # Verificar que el candidato pertenece al tenant
        cursor.execute("SELECT id_afiliado FROM Afiliados WHERE id_afiliado = %s AND tenant_id = %s", (target_id, tenant_id))
        if not cursor.fetchone():
            return json.dumps({"error": "Candidato no encontrado en su organización"})
            
        # Insertar registro de pago (asumiendo tabla Pagos o similar)
        # Nota: Ajustar según esquema real de base de datos
        sql = """
            INSERT INTO Pagos (id_afiliado, monto, tipo_pago, descripcion, fecha_pago, tenant_id)
            VALUES (%s, %s, %s, %s, NOW(), %s)
        """
        cursor.execute(sql, (target_id, amount, payment_type, description, tenant_id))
        conn.commit()
        
        return json.dumps({
            "success": True,
            "message": f"Pago de {amount} registrado exitosamente para el candidato {target_id}",
            "tenant_id": tenant_id
        })
        
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error en register_payment_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

def generate_predictive_analytics(tenant_id: int, analysis_type: str, 
                                 candidate_id: int = None, vacancy_id: int = None):
    """
    Genera análisis IA predictivo filtrando por tenant_id
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        if analysis_type == "hiring_probability":
            if not candidate_id or not vacancy_id:
                return json.dumps({"error": "Se requiere candidate_id y vacancy_id para este análisis"})
                
            # Verificar pertenencia
            cursor.execute("SELECT id_afiliado FROM Afiliados WHERE id_afiliado = %s AND tenant_id = %s", (candidate_id, tenant_id))
            if not cursor.fetchone(): return json.dumps({"error": "Candidato denegado"})
            
            cursor.execute("SELECT id_vacante FROM Vacantes WHERE id_vacante = %s AND tenant_id = %s", (vacancy_id, tenant_id))
            if not cursor.fetchone(): return json.dumps({"error": "Vacante denegada"})
            
            # Simulación de lógica predictiva (o llamada a modelo real)
            probability = 75 if candidate_id % 2 == 0 else 45 # Lógica de ejemplo
            
            return json.dumps({
                "probability": f"{probability}%",
                "factors": ["Experiencia en sector", "Ubicación geográfica", "Historial de postulaciones"],
                "recommendation": "Proceder a entrevista técnica" if probability > 60 else "Revisar más candidatos",
                "tenant_id": tenant_id
            })
            
        return json.dumps({"error": f"Análisis '{analysis_type}' no implementado aún"})
        
    except Exception as e:
        app.logger.error(f"Error en generate_predictive_analytics: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

def export_data_multi_tenant(tenant_id: int, export_type: str, 
                            format_type: str = "excel", **filters):
    """
    Exportación avanzada de datos del tenant con múltiples formatos
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        if export_type == "candidates":
            # Exportar candidatos con filtros
            base_query = """
                SELECT a.id_afiliado, a.nombre_completo, a.email, a.telefono, 
                       a.experiencia, a.ciudad, a.estado, a.fecha_registro,
                       COUNT(p.id_postulacion) as total_postulaciones,
                       COUNT(c.id_contratado) as contrataciones
                FROM Afiliados a
                LEFT JOIN Postulaciones p ON a.id_afiliado = p.id_afiliado
                LEFT JOIN Contratados c ON a.id_afiliado = c.id_afiliado
                WHERE a.tenant_id = %s
            """
            params = [tenant_id]
            
            # Aplicar filtros
            if filters.get('city'):
                base_query += " AND a.ciudad = %s"
                params.append(filters['city'])
            
            if filters.get('date_from'):
                base_query += " AND a.fecha_registro >= %s"
                params.append(filters['date_from'])
                
            base_query += " GROUP BY a.id_afiliado ORDER BY a.fecha_registro DESC"
            
            cursor.execute(base_query, params)
            candidates_data = cursor.fetchall()
            
        elif export_type == "vacancies":
            # Exportar vacantes
            cursor.execute("""
                SELECT v.id_vacante, v.cargo_solicitado, c.empresa, v.ciudad, 
                       v.salario, v.estado, v.fecha_apertura,
                       COUNT(p.id_postulacion) as total_postulaciones,
                       COUNT(co.id_contratado) as contrataciones
                FROM Vacantes v
                JOIN Clientes c ON v.id_cliente = c.id_cliente
                LEFT JOIN Postulaciones p ON v.id_vacante = p.id_vacante
                LEFT JOIN Contratados co ON p.id_afiliado = co.id_afiliado
                WHERE v.tenant_id = %s
                GROUP BY v.id_vacante
                ORDER BY v.fecha_apertura DESC
            """, (tenant_id,))
            
            candidates_data = cursor.fetchall()
            
        elif export_type == "reports":
            # Exportar reportes completos
            cursor.execute("""
                SELECT 
                    'Candidatos' as categoria,
                    COUNT(*) as total,
                    COUNT(CASE WHEN a.estado = 'Activo' THEN 1 END) as activos
                FROM Afiliados a WHERE a.tenant_id = %s
                UNION ALL
                SELECT 
                    'Vacantes' as categoria,
                    COUNT(*) as total,
                    COUNT(CASE WHEN v.estado = 'Abierta' THEN 1 END) as activos
                FROM Vacantes v WHERE v.tenant_id = %s
                UNION ALL
                SELECT 
                    'Postulaciones' as categoria,
                    COUNT(*) as total,
                    COUNT(CASE WHEN p.estado = 'Recibida' THEN 1 END) as activos
                FROM Postulaciones p 
                JOIN Vacantes v ON p.id_vacante = v.id_vacante
                WHERE v.tenant_id = %s
            """, (tenant_id, tenant_id, tenant_id))
            
            candidates_data = cursor.fetchall()
            
        else:
            return json.dumps({"error": f"Tipo de exportación '{export_type}' no soportado"})
        
        # Convertir fechas para JSON
        for item in candidates_data:
            for key, value in item.items():
                if isinstance(value, (datetime, date)):
                    item[key] = value.isoformat()
        
        # Preparar respuesta según formato
        export_info = {
            "export_type": export_type,
            "format_type": format_type,
            "total_records": len(candidates_data),
            "data": candidates_data,
            "filters_applied": filters,
            "generated_at": datetime.now().isoformat(),
            "tenant_id": tenant_id
        }
        
        if format_type == "excel":
            export_info["message"] = f"Datos preparados para exportar a Excel: {len(candidates_data)} registros"
            export_info["download_ready"] = True
        elif format_type == "csv":
            export_info["message"] = f"Datos preparados para exportar a CSV: {len(candidates_data)} registros"
            export_info["download_ready"] = True
        elif format_type == "json":
            export_info["message"] = f"Datos en formato JSON: {len(candidates_data)} registros"
        
        return json.dumps({
            "success": True,
            **export_info
        })
        
    except Exception as e:
        app.logger.error(f"Error en export_data_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

def bulk_operations_multi_tenant(tenant_id: int, operation_type: str, 
                                target_ids: list = None, **operation_data):
    """
    Operaciones masivas inteligentes para el tenant actual
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        if operation_type == "bulk_postulate":
            # Postular múltiples candidatos a una vacante
            vacancy_id = operation_data.get('vacancy_id')
            candidate_ids = target_ids or []
            
            if not vacancy_id or not candidate_ids:
                return json.dumps({"error": "Se requiere vacancy_id y candidate_ids"})
            
            # Verificar que la vacante pertenece al tenant
            cursor.execute("""
                SELECT id_vacante FROM Vacantes 
                WHERE id_vacante = %s AND tenant_id = %s
            """, (vacancy_id, tenant_id))
            
            if not cursor.fetchone():
                return json.dumps({"error": "Vacante no encontrada o no pertenece a su organización"})
            
            successful_postulations = []
            failed_postulations = []
            
            for candidate_id in candidate_ids:
                try:
                    # Verificar que el candidato pertenece al tenant
                    cursor.execute("""
                        SELECT nombre_completo FROM Afiliados 
                        WHERE id_afiliado = %s AND tenant_id = %s
                    """, (candidate_id, tenant_id))
                    
                    candidate = cursor.fetchone()
                    if not candidate:
                        failed_postulations.append({"candidate_id": candidate_id, "error": "Candidato no encontrado"})
                        continue
                    
                    # Verificar si ya está postulado
                    cursor.execute("""
                        SELECT id_postulacion FROM Postulaciones 
                        WHERE id_afiliado = %s AND id_vacante = %s
                    """, (candidate_id, vacancy_id))
                    
                    if cursor.fetchone():
                        failed_postulations.append({"candidate_id": candidate_id, "error": "Ya postulado"})
                        continue
                    
                    # Crear postulación
                    cursor.execute("""
                        INSERT INTO Postulaciones (id_afiliado, id_vacante, fecha_aplicacion, estado, comentarios, tenant_id)
                        VALUES (%s, %s, NOW(), 'Recibida', 'Postulación masiva por bot', %s)
                    """, (candidate_id, vacancy_id, tenant_id))
                    
                    successful_postulations.append({
                        "candidate_id": candidate_id,
                        "candidate_name": candidate['nombre_completo']
                    })
                    
                except Exception as e:
                    failed_postulations.append({"candidate_id": candidate_id, "error": str(e)})
            
            conn.commit()
            
            return json.dumps({
                "success": True,
                "operation_type": "bulk_postulate",
                "vacancy_id": vacancy_id,
                "successful_postulations": successful_postulations,
                "failed_postulations": failed_postulations,
                "total_successful": len(successful_postulations),
                "total_failed": len(failed_postulations),
                "message": f"Postulación masiva completada: {len(successful_postulations)} exitosas, {len(failed_postulations)} fallidas",
                "tenant_id": tenant_id
            })
            
        elif operation_type == "bulk_status_update":
            # Actualizar estado de múltiples postulaciones
            postulation_ids = target_ids or []
            new_status = operation_data.get('new_status')
            
            if not postulation_ids or not new_status:
                return json.dumps({"error": "Se requiere postulation_ids y new_status"})
            
            successful_updates = []
            failed_updates = []
            
            for postulation_id in postulation_ids:
                try:
                    # Verificar que la postulación pertenece al tenant
                    cursor.execute("""
                        SELECT p.id_postulacion, a.nombre_completo
                        FROM Postulaciones p
                        JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
                        JOIN Vacantes v ON p.id_vacante = v.id_vacante
                        WHERE p.id_postulacion = %s AND v.tenant_id = %s
                    """, (postulation_id, tenant_id))
                    
                    postulation = cursor.fetchone()
                    if not postulation:
                        failed_updates.append({"postulation_id": postulation_id, "error": "Postulación no encontrada"})
                        continue
                    
                    # Actualizar estado
                    cursor.execute("""
                        UPDATE Postulaciones SET estado = %s 
                        WHERE id_postulacion = %s
                    """, (new_status, postulation_id))
                    
                    successful_updates.append({
                        "postulation_id": postulation_id,
                        "candidate_name": postulation['nombre_completo']
                    })
                    
                except Exception as e:
                    failed_updates.append({"postulation_id": postulation_id, "error": str(e)})
            
            conn.commit()
            
            return json.dumps({
                "success": True,
                "operation_type": "bulk_status_update",
                "new_status": new_status,
                "successful_updates": successful_updates,
                "failed_updates": failed_updates,
                "total_successful": len(successful_updates),
                "total_failed": len(failed_updates),
                "message": f"Actualización masiva completada: {len(successful_updates)} exitosas, {len(failed_updates)} fallidas",
                "tenant_id": tenant_id
            })
            
        else:
            return json.dumps({"error": f"Tipo de operación '{operation_type}' no soportado"})
        
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error en bulk_operations_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

# AGENTS API
@app.route('/api/agents/deploy', methods=['POST'])
@token_required
def deploy_tenant_agent_endpoint():
    # Import dinámico para no romper Gunicorn
    from agent_orchestrator import orchestrator
    tenant_id = get_current_tenant_id()
    user_data = g.current_user
    user_id = user_data.get('user_id')
    if not is_admin(user_id, tenant_id):
        return jsonify({"success": False, "message": "No tienes permisos"}), 403
    conn = get_db_connection()
    try:
        api_keys = public_api_service.get_api_keys_by_tenant(conn, tenant_id)
        bot_key = next((k for k in api_keys if k['nombre_descriptivo'] == 'ESC_BOT_KEY'), None)
        if not bot_key:
            res = public_api_service.create_api_key(conn, tenant_id, "ESC_BOT_KEY", "Key bot", user_id)
            api_key_str = res['api_key']
        else:
            api_key_str = bot_key['api_key']
        success, info = orchestrator.deploy_agent(
            tenant_id=tenant_id, tenant_api_key=api_key_str,
            llm_api_key=os.getenv('OPENAI_API_KEY'),
            crm_url=os.getenv('ESC_CRM_INTERNAL_URL', 'http://esc-backend:5000')
        )
        return jsonify({"success": success, "info": info})
    finally: conn.close()

@app.route('/api/agents/chat', methods=['POST'])
@token_required
def proxy_agent_chat():
    from agent_orchestrator import orchestrator
    tenant_id = get_current_tenant_id()
    data = request.get_json()
    message = data.get('message')
    agent_url = f"http://esc-agent-tenant-{tenant_id}:18791/chat"
    try:
        response = requests.post(agent_url, json={"message": message}, timeout=60)
        return jsonify(response.json())
    except:
        return jsonify({"error": "Agente no responde"}), 503

@app.route('/api/agents/status', methods=['GET'])
@token_required
def get_agent_status():
    tenant_id = get_current_tenant_id()
    container_name = f"esc-agent-tenant-{tenant_id}"
    try:
        import subprocess
        result = subprocess.run(["docker", "inspect", "-f", "{{.State.Status}}", container_name], capture_output=True, text=True)
        status = result.stdout.strip() if result.returncode == 0 else "inactive"
        return jsonify({"tenant_id": tenant_id, "status": status})
    except: return jsonify({"status": "error"})

@app.route('/api/public/vacancies', methods=['GET'])
@public_api_key_required
def get_public_vacancies():
    tenant_id = g.tenant_id
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_vacante, cargo_solicitado, requisitos, ciudad FROM Vacantes WHERE tenant_id = %s AND estado = 'Abierta'", (tenant_id,))
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        conn.close()

@app.route('/api/public/candidates', methods=['GET'])
@public_api_key_required
def get_public_candidates():
    tenant_id = g.tenant_id
    identity = request.args.get('identity')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_afiliado, nombre_completo FROM Afiliados WHERE tenant_id = %s AND identidad = %s", (tenant_id, identity))
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        conn.close()

@app.route('/api/public/applications', methods=['POST'])
@public_api_key_required
def post_public_application():
    tenant_id = g.tenant_id
    data = request.get_json()
    vacancy_id = data.get('vacancy_id')
    candidate = data.get('candidate', {})
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_afiliado FROM Afiliados WHERE identidad = %s AND tenant_id = %s", (candidate['identidad'], tenant_id))
        res = cursor.fetchone()
        candidate_id = res['id_afiliado'] if res else None
        if not candidate_id:
            cursor.execute("INSERT INTO Afiliados (tenant_id, nombre_completo, identidad, telefono, creado_en) VALUES (%s, %s, %s, %s, NOW())", 
                         (tenant_id, candidate.get('nombre'), candidate['identidad'], candidate.get('telefono')))
            candidate_id = cursor.lastrowid
        cursor.execute("INSERT INTO Postulaciones (tenant_id, id_afiliado, id_vacante, fecha_aplicacion, estado) VALUES (%s, %s, %s, NOW(), 'Recibida')", 
                     (tenant_id, candidate_id, vacancy_id))
        conn.commit()
        return jsonify({"success": True, "candidate_id": candidate_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
