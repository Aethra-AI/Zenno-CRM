# -*- coding: utf-8 -*-
import os
import requests
import json
import time
from flask import Flask, jsonify, request, Response, send_file
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
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
import logging
from logging.handlers import RotatingFileHandler
import traceback
from functools import wraps
import uuid
import re
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

# Reemplaza la línea CORS(app) con este bloque
CORS(app, 
     # Aplica esta configuración a todas las rutas que empiecen con /api/ o /public-api/
     resources={r"/*": {"origins": "*"}},
     # Permite explícitamente los métodos que usamos, incluyendo OPTIONS
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     # LA LÍNEA MÁS IMPORTANTE: Permite explícitamente la cabecera de autorización
     allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
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
                            "analysis_type": {"type": "string", "description": "Tipo: 'candidate_success', 'vacancy_performance'"},
                            "position_type": {"type": "string", "description": "Tipo de posición para análisis específico"}
                        }, 
                        "required": ["analysis_type"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "manage_clients_intelligent", 
                    "description": "Gestión inteligente de clientes con sugerencias basadas en historial",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "action": {"type": "string", "description": "Acción: 'get_suggestions', 'client_stats'"},
                            "client_id": {"type": "integer", "description": "ID del cliente para sugerencias específicas"}
                        }, 
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "schedule_interviews_intelligent", 
                    "description": "Programa entrevistas inteligentes con detección de conflictos",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "postulation_id": {"type": "integer", "description": "ID de la postulación"},
                            "interview_date": {"type": "string", "description": "Fecha en formato YYYY-MM-DD"},
                            "interview_time": {"type": "string", "description": "Hora en formato HH:MM"},
                            "interviewer": {"type": "string", "description": "Nombre del entrevistador"},
                            "notes": {"type": "string", "description": "Notas adicionales"}
                        }, 
                        "required": ["postulation_id", "interview_date", "interview_time", "interviewer"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "get_smart_recommendations", 
                    "description": "Obtiene recomendaciones inteligentes (solo cuando el usuario las pida)",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "context": {"type": "string", "description": "Contexto: 'vacancy_candidates', 'candidate_vacancies'"},
                            "vacancy_id": {"type": "integer", "description": "ID de vacante para recomendar candidatos"},
                            "candidate_id": {"type": "integer", "description": "ID de candidato para recomendar vacantes"}
                        }, 
                        "required": ["context"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "advanced_integrations", 
                    "description": "Integraciones premium con servicios externos (LinkedIn, Google Calendar, bolsas de trabajo, Slack, ATS)",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "integration_type": {"type": "string", "description": "Tipo: 'linkedin_search', 'google_calendar', 'job_boards', 'slack_notifications', 'ats_sync'"},
                            "action": {"type": "string", "description": "Acción específica para la integración"},
                            "search_term": {"type": "string", "description": "Término de búsqueda para LinkedIn"},
                            "location": {"type": "string", "description": "Ubicación para búsquedas"},
                            "vacancy_id": {"type": "integer", "description": "ID de vacante para publicar en bolsas de trabajo"},
                            "message": {"type": "string", "description": "Mensaje para notificaciones Slack"}
                        }, 
                        "required": ["integration_type"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "export_data_multi_tenant", 
                    "description": "Exportación avanzada de datos del tenant en múltiples formatos",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "export_type": {"type": "string", "description": "Tipo: 'candidates', 'vacancies', 'reports'"},
                            "format_type": {"type": "string", "description": "Formato: 'excel', 'csv', 'json'"},
                            "city": {"type": "string", "description": "Filtro por ciudad"},
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
                    "description": "Operaciones masivas inteligentes (postulaciones masivas, actualizaciones de estado)",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "operation_type": {"type": "string", "description": "Tipo: 'bulk_postulate', 'bulk_status_update'"},
                            "target_ids": {"type": "array", "items": {"type": "integer"}, "description": "Lista de IDs objetivo"},
                            "vacancy_id": {"type": "integer", "description": "ID de vacante para postulaciones masivas"},
                            "new_status": {"type": "string", "description": "Nuevo estado para actualizaciones masivas"}
                        }, 
                        "required": ["operation_type"]
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
        tool_calls = response_message.tool_calls

        if tool_calls:
            # Mapeo de funciones disponibles
            available_functions = {
                "search_candidates_multi_tenant": search_candidates_multi_tenant,
                "get_vacancies_multi_tenant": get_vacancies_multi_tenant,
                "postulate_candidate_multi_tenant": postulate_candidate_multi_tenant,
                "update_application_status_multi_tenant": update_application_status_multi_tenant,
                "get_dashboard_stats_multi_tenant": get_dashboard_stats_multi_tenant,
                "create_whatsapp_campaign_multi_tenant": create_whatsapp_campaign_multi_tenant,
                "register_payment_multi_tenant": register_payment_multi_tenant,
                # Fase 2: Herramientas de Inteligencia
                "generate_predictive_analytics": generate_predictive_analytics,
                "manage_clients_intelligent": manage_clients_intelligent,
                "schedule_interviews_intelligent": schedule_interviews_intelligent,
                "get_smart_recommendations": get_smart_recommendations,
                # Fase 3: Herramientas Premium
                "advanced_integrations": advanced_integrations,
                "export_data_multi_tenant": export_data_multi_tenant,
                "bulk_operations_multi_tenant": bulk_operations_multi_tenant,
            }
            
            messages.append(response_message)
            
            # Ejecutar herramientas
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                function_to_call = available_functions.get(function_name)
                
                if function_to_call:
                    # Pasar tenant_id a todas las funciones
                    function_args['tenant_id'] = tenant_id
                    function_response = function_to_call(**function_args)
                else:
                    function_response = json.dumps({"error": f"Función '{function_name}' no encontrada."})
                
                messages.append({
                    "tool_call_id": tool_call.id, 
                    "role": "tool", 
                    "name": function_name,
                    "content": function_response if isinstance(function_response, str) else json.dumps(function_response),
                })
            
            # Respuesta final
            final_response_message = openai_client.chat.completions.create(
                model="gpt-4o", 
                messages=messages
            ).choices[0].message.content
            
            return jsonify({
                "type": "text_response", 
                "data": final_response_message,
                "tenant_id": tenant_id,
                "user_role": user_role
            })
        else:
            return jsonify({
                "type": "text_response", 
                "data": response_message.content,
                "tenant_id": tenant_id,
                "user_role": user_role
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        app.logger.error(f"Error en assistant_command: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ===============================================================
# 🛠️ HERRAMIENTAS DEL BOT MULTI-TENANT
# ===============================================================

def search_candidates_multi_tenant(tenant_id: int, term: str = None, tags: str = None, 
                                 experience: str = None, city: str = None, recency_days: int = None,
                                 candidate_id: int = None):
    """Busca candidatos del tenant actual con aislamiento de datos"""
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Si se busca por ID específico, usar consulta directa
        if candidate_id:
            cursor.execute("""
                SELECT a.id_afiliado, a.nombre_completo, a.email, a.telefono, a.ciudad, 
                       a.experiencia, a.fecha_registro, a.estado
                FROM Afiliados a
                WHERE a.tenant_id = %s AND a.id_afiliado = %s
            """, (tenant_id, candidate_id))
            candidates = cursor.fetchall()
            
            # Convertir fechas para JSON
            for candidate in candidates:
                if candidate.get('fecha_registro'):
                    candidate['fecha_registro'] = candidate['fecha_registro'].isoformat()
            
            return json.dumps({
                "success": True,
                "data": candidates,
                "count": len(candidates),
                "tenant_id": tenant_id,
                "search_type": "by_id"
            })
        
        # Construir consulta con filtro de tenant
        base_query = """
            SELECT a.id_afiliado, a.nombre_completo, a.email, a.telefono, a.ciudad, 
                   a.experiencia, a.fecha_registro, a.estado
            FROM Afiliados a
            WHERE a.tenant_id = %s
        """
        params = [tenant_id]
        
        # Filtros adicionales
        if term:
            base_query += " AND (a.nombre_completo LIKE %s OR a.email LIKE %s OR a.ciudad LIKE %s)"
            params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])
        
        if city:
            base_query += " AND a.ciudad LIKE %s"
            params.append(f"%{city}%")
        
        if experience:
            # Si experience es un número, filtrar por años de experiencia
            if experience.isdigit():
                base_query += " AND a.experiencia >= %s"
                params.append(int(experience))
            else:
                # Si es texto, buscar en el campo experiencia como texto
                base_query += " AND a.experiencia LIKE %s"
                params.append(f"%{experience}%")
        
        if recency_days:
            base_query += " AND a.fecha_registro >= DATE_SUB(NOW(), INTERVAL %s DAY)"
            params.append(recency_days)
        
        base_query += " ORDER BY a.fecha_registro DESC LIMIT 50"
        
        cursor.execute(base_query, params)
        candidates = cursor.fetchall()
        
        # Convertir fechas para JSON
        for candidate in candidates:
            if candidate.get('fecha_registro'):
                candidate['fecha_registro'] = candidate['fecha_registro'].isoformat()
        
        return json.dumps({
            "success": True,
            "data": candidates,
            "count": len(candidates),
            "tenant_id": tenant_id
        })
        
    except Exception as e:
        app.logger.error(f"Error en search_candidates_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


def get_vacancies_multi_tenant(tenant_id: int, city: str = None, keyword: str = None):
    """Obtiene vacantes activas del tenant actual con aislamiento de datos"""
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Construir consulta con filtro de tenant
        base_query = """
            SELECT v.id_vacante, v.cargo_solicitado, v.ciudad, v.salario, v.requisitos,
                   v.fecha_apertura, v.estado, c.empresa
            FROM Vacantes v
            JOIN Clientes c ON v.id_cliente = c.id_cliente
            WHERE v.tenant_id = %s AND v.estado = 'Abierta'
        """
        params = [tenant_id]
        
        # Filtros adicionales
        if city:
            base_query += " AND v.ciudad LIKE %s"
            params.append(f"%{city}%")
        
        if keyword:
            base_query += " AND (v.cargo_solicitado LIKE %s OR v.requisitos LIKE %s OR c.empresa LIKE %s)"
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
        
        base_query += " ORDER BY v.fecha_apertura DESC LIMIT 50"
        
        cursor.execute(base_query, params)
        vacancies = cursor.fetchall()
        
        # Convertir fechas para JSON
        for vacancy in vacancies:
            if vacancy.get('fecha_apertura'):
                vacancy['fecha_apertura'] = vacancy['fecha_apertura'].isoformat()
        
        return json.dumps({
            "success": True,
            "data": vacancies,
            "count": len(vacancies),
            "tenant_id": tenant_id
        })
        
    except Exception as e:
        app.logger.error(f"Error en get_vacancies_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


def postulate_candidate_multi_tenant(tenant_id: int, vacancy_id: int, candidate_id: int = None, 
                                   identity_number: str = None, comments: str = ""):
    """Postula un candidato del tenant actual a una vacante con validación de tenant"""
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Verificar que la vacante pertenece al tenant
        cursor.execute("""
            SELECT id_vacante FROM Vacantes 
            WHERE id_vacante = %s AND tenant_id = %s
        """, (vacancy_id, tenant_id))
        
        if not cursor.fetchone():
            return json.dumps({"error": "Vacante no encontrada o no pertenece a su organización"})
        
        # Buscar candidato
        final_candidate_id = _get_candidate_id(conn, candidate_id, identity_number)
        if not final_candidate_id:
            return json.dumps({"error": "No se pudo encontrar al candidato con los datos proporcionados"})
        
        # Verificar que el candidato pertenece al tenant
        cursor.execute("""
            SELECT id_afiliado FROM Afiliados 
            WHERE id_afiliado = %s AND tenant_id = %s
        """, (final_candidate_id, tenant_id))
        
        if not cursor.fetchone():
            return json.dumps({"error": "Candidato no encontrado o no pertenece a su organización"})
        
        # Verificar si ya existe la postulación
        cursor.execute("""
            SELECT id_postulacion FROM Postulaciones 
            WHERE id_afiliado = %s AND id_vacante = %s
        """, (final_candidate_id, vacancy_id))
        
        if cursor.fetchone():
            return json.dumps({"error": "El candidato ya está postulado a esta vacante"})
        
        # Crear la postulación
        cursor.execute("""
            INSERT INTO Postulaciones (id_afiliado, id_vacante, fecha_aplicacion, estado, comentarios, tenant_id)
            VALUES (%s, %s, NOW(), 'Recibida', %s, %s)
        """, (final_candidate_id, vacancy_id, comments, tenant_id))
        
        conn.commit()
        
        return json.dumps({
            "success": True,
            "message": f"Candidato postulado exitosamente a la vacante {vacancy_id}",
            "candidate_id": final_candidate_id,
            "vacancy_id": vacancy_id,
            "tenant_id": tenant_id
        })
        
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error en postulate_candidate_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


def update_application_status_multi_tenant(tenant_id: int, postulation_id: int, new_status: str):
    """Actualiza el estado de una postulación del tenant actual con validación de tenant"""
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor()
    try:
        # Verificar que la postulación pertenece al tenant
        cursor.execute("""
            SELECT p.id_postulacion, p.id_afiliado, p.id_vacante, v.id_cliente
            FROM Postulaciones p
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE p.id_postulacion = %s AND v.tenant_id = %s
        """, (postulation_id, tenant_id))
        
        postulacion_data = cursor.fetchone()
        if not postulacion_data:
            return json.dumps({"error": "Postulación no encontrada o no pertenece a su organización"})
        
        # Actualizar el estado
        cursor.execute("""
            UPDATE Postulaciones SET estado = %s 
            WHERE id_postulacion = %s
        """, (new_status, postulation_id))
        
        # Si el nuevo estado es "Contratado", registrar en Contratados
        if new_status.lower() in ['contratado', 'hired', 'aceptado']:
            id_afiliado, id_vacante, id_cliente = postulacion_data[1], postulacion_data[2], postulacion_data[3]
            
            # Verificar si ya existe en Contratados
            cursor.execute("""
                SELECT id_contratado FROM Contratados 
                WHERE id_afiliado = %s AND id_vacante = %s
            """, (id_afiliado, id_vacante))
            
            if not cursor.fetchone():
                # Insertar en Contratados
                cursor.execute("""
                    INSERT INTO Contratados (id_afiliado, id_vacante, id_cliente, fecha_contratacion, estado, tenant_id)
                    VALUES (%s, %s, %s, NOW(), 'Activo', %s)
                """, (id_afiliado, id_vacante, id_cliente, tenant_id))
        
        conn.commit()
        
        return json.dumps({
            "success": True,
            "message": f"Estado de postulación actualizado a {new_status}",
            "postulation_id": postulation_id,
            "new_status": new_status,
            "tenant_id": tenant_id
        })
        
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error en update_application_status_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


def get_dashboard_stats_multi_tenant(tenant_id: int, report_type: str = "kpi"):
    """Obtiene estadísticas del dashboard del tenant actual"""
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        if report_type == "kpi":
            # Estadísticas básicas del tenant
            stats = {}
            
            # Total candidatos
            cursor.execute("SELECT COUNT(*) as total FROM Afiliados WHERE tenant_id = %s", (tenant_id,))
            stats['total_candidates'] = cursor.fetchone()['total']
            
            # Total vacantes activas
            cursor.execute("SELECT COUNT(*) as total FROM Vacantes WHERE tenant_id = %s AND estado = 'Abierta'", (tenant_id,))
            stats['active_vacancies'] = cursor.fetchone()['total']
            
            # Total postulaciones
            cursor.execute("SELECT COUNT(*) as total FROM Postulaciones WHERE tenant_id = %s", (tenant_id,))
            stats['total_applications'] = cursor.fetchone()['total']
            
            # Postulaciones por estado
            cursor.execute("""
                SELECT estado, COUNT(*) as count 
                FROM Postulaciones 
                WHERE tenant_id = %s 
                GROUP BY estado
            """, (tenant_id,))
            stats['applications_by_status'] = {row['estado']: row['count'] for row in cursor.fetchall()}
            
            # Total contratados
            cursor.execute("SELECT COUNT(*) as total FROM Contratados WHERE tenant_id = %s", (tenant_id,))
            stats['total_hired'] = cursor.fetchone()['total']
            
            return json.dumps({
                "success": True,
                "data": stats,
                "report_type": report_type,
                "tenant_id": tenant_id
            })
        
        else:
            return json.dumps({"error": f"Tipo de reporte '{report_type}' no soportado"})
        
    except Exception as e:
        app.logger.error(f"Error en get_dashboard_stats_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


def create_whatsapp_campaign_multi_tenant(tenant_id: int, message_body: str = None, 
                                         candidate_ids: str = None, vacancy_id: int = None, 
                                         template_type: str = "custom", **campaign_options):
    """
    Crea campañas de WhatsApp inteligentes con soporte multi-tenant
    Detecta automáticamente si usar API oficial o WhatsApp Web según configuración del tenant
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Verificar configuración de WhatsApp del tenant
        cursor.execute("""
            SELECT config_type, phone_number, status 
            FROM WhatsApp_Config 
            WHERE tenant_id = %s AND status = 'active'
        """, (tenant_id,))
        
        whatsapp_config = cursor.fetchone()
        if not whatsapp_config:
            return json.dumps({
                "error": "No hay configuración de WhatsApp activa para su organización",
                "action_required": "Configure WhatsApp en Configuración > Integraciones"
            })
        
        # Obtener candidatos objetivo
        recipients = []
        
        if candidate_ids:
            # Buscar por lista de IDs
            ids_list = [id.strip() for id in candidate_ids.split(',')]
            for candidate_id in ids_list:
                if candidate_id.isdigit():
                    cursor.execute("""
                        SELECT id_afiliado, nombre_completo, telefono 
                        FROM Afiliados 
                        WHERE id_afiliado = %s AND tenant_id = %s
                    """, (int(candidate_id), tenant_id))
                    candidate = cursor.fetchone()
                    if candidate:
                        recipients.append(candidate)
        
        elif vacancy_id:
            # Buscar candidatos postulados a una vacante específica
            cursor.execute("""
                SELECT DISTINCT a.id_afiliado, a.nombre_completo, a.telefono
                FROM Afiliados a
                JOIN Postulaciones p ON a.id_afiliado = p.id_afiliado
                JOIN Vacantes v ON p.id_vacante = v.id_vacante
                WHERE v.id_vacante = %s AND v.tenant_id = %s AND a.tenant_id = %s
            """, (vacancy_id, tenant_id, tenant_id))
            recipients = cursor.fetchall()
        
        else:
            return json.dumps({
                "error": "Debe especificar candidate_ids o vacancy_id para la campaña"
            })
        
        if not recipients:
            return json.dumps({
                "error": "No se encontraron candidatos válidos para la campaña"
            })
        
        # Determinar mensaje según tipo de plantilla
        if not message_body:
            if template_type == "vacancy_invitation":
                message_body = "Hola [nombre], tenemos una nueva oportunidad laboral que podría interesarte. ¿Te gustaría conocer más detalles?"
            elif template_type == "interview_reminder":
                message_body = "Hola [nombre], te recordamos tu entrevista programada. ¡Te esperamos!"
            elif template_type == "status_update":
                message_body = "Hola [nombre], hay una actualización sobre tu postulación. Te contactaremos pronto."
            else:
                message_body = "Hola [nombre], nos comunicamos contigo desde nuestro equipo de reclutamiento."
        
        # Preparar lista de destinatarios con datos limpios
        campaign_recipients = []
        for recipient in recipients:
            clean_phone = clean_phone_number(recipient['telefono'])
            if clean_phone and len(clean_phone) >= 10:
                campaign_recipients.append({
                    "id_afiliado": recipient['id_afiliado'],
                    "nombre_completo": recipient['nombre_completo'],
                    "telefono": clean_phone,
                    "mensaje_personalizado": message_body.replace('[nombre]', recipient['nombre_completo'])
                })
        
        return json.dumps({
            "success": True,
            "whatsapp_method": whatsapp_config['config_type'],  # 'api' o 'web'
            "total_recipients": len(campaign_recipients),
            "recipients": campaign_recipients,
            "message_template": message_body,
            "message": f"Campaña preparada para {len(campaign_recipients)} candidatos usando {whatsapp_config['config_type'].upper()}",
            "tenant_id": tenant_id
        })
        
    except Exception as e:
        app.logger.error(f"Error en create_whatsapp_campaign_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


def register_payment_multi_tenant(tenant_id: int, hired_candidate_id: int = None, 
                                 candidate_id: int = None, amount: float = None, 
                                 payment_type: str = "commission", **payment_data):
    """
    Registra pagos asociados a candidatos contratados con validación multi-tenant
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Determinar ID del candidato contratado
        if hired_candidate_id:
            # Verificar que el contratado pertenece al tenant
            cursor.execute("""
                SELECT c.id_contratado, c.id_afiliado, a.nombre_completo, cl.empresa
                FROM Contratados c
                JOIN Afiliados a ON c.id_afiliado = a.id_afiliado
                JOIN Clientes cl ON c.id_cliente = cl.id_cliente
                WHERE c.id_contratado = %s AND c.tenant_id = %s
            """, (hired_candidate_id, tenant_id))
            
        elif candidate_id:
            # Buscar si el candidato está contratado en este tenant
            cursor.execute("""
                SELECT c.id_contratado, c.id_afiliado, a.nombre_completo, cl.empresa
                FROM Contratados c
                JOIN Afiliados a ON c.id_afiliado = a.id_afiliado
                JOIN Clientes cl ON c.id_cliente = cl.id_cliente
                WHERE c.id_afiliado = %s AND c.tenant_id = %s
                ORDER BY c.fecha_contratacion DESC
                LIMIT 1
            """, (candidate_id, tenant_id))
        else:
            return json.dumps({
                "error": "Debe especificar hired_candidate_id o candidate_id"
            })
        
        hired_candidate = cursor.fetchone()
        if not hired_candidate:
            return json.dumps({
                "error": "Candidato contratado no encontrado o no pertenece a su organización"
            })
        
        # Validar monto
        if not amount or amount <= 0:
            return json.dumps({
                "error": "El monto del pago debe ser mayor a cero"
            })
        
        # Registrar el pago (usando tabla existente si existe, o crear log)
        cursor.execute("""
            INSERT INTO UserActivityLog (user_id, action, details, ip_address, created_at)
            VALUES (1, 'payment_registered', %s, 'bot', NOW())
        """, (f'Pago registrado: ${amount} para candidato {hired_candidate["nombre_completo"]} (ID: {hired_candidate["id_afiliado"]})'))
        
        conn.commit()
        
        return json.dumps({
            "success": True,
            "candidate_name": hired_candidate['nombre_completo'],
            "company": hired_candidate['empresa'],
            "amount": amount,
            "payment_type": payment_type,
            "message": f"Pago de ${amount} registrado exitosamente para {hired_candidate['nombre_completo']}",
            "tenant_id": tenant_id
        })
        
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error en register_payment_multi_tenant: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


# ===============================================================
# 🧠 HERRAMIENTAS DE FASE 2: INTELIGENCIA
# ===============================================================

def generate_predictive_analytics(tenant_id: int, analysis_type: str = "candidate_success", 
                                 position_type: str = None, **params):
    """
    Análisis predictivo avanzado para candidatos del tenant actual
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        if analysis_type == "candidate_success":
            # Análisis de éxito de candidatos basado en historial
            cursor.execute("""
                SELECT 
                    a.experiencia,
                    a.ciudad,
                    COUNT(c.id_contratado) as contrataciones_exitosas,
                    COUNT(p.id_postulacion) as total_postulaciones,
                    ROUND((COUNT(c.id_contratado) / COUNT(p.id_postulacion)) * 100, 2) as tasa_exito
                FROM Afiliados a
                LEFT JOIN Postulaciones p ON a.id_afiliado = p.id_afiliado
                LEFT JOIN Contratados c ON a.id_afiliado = c.id_afiliado
                WHERE a.tenant_id = %s
                GROUP BY a.experiencia, a.ciudad
                HAVING COUNT(p.id_postulacion) > 0
                ORDER BY tasa_exito DESC
                LIMIT 10
            """, (tenant_id,))
            
            success_patterns = cursor.fetchall()
            
            # Encontrar candidatos que coinciden con patrones exitosos
            if success_patterns and position_type:
                cursor.execute("""
                    SELECT a.id_afiliado, a.nombre_completo, a.experiencia, a.ciudad, a.email
                    FROM Afiliados a
                    WHERE a.tenant_id = %s 
                    AND a.experiencia >= %s
                    AND a.ciudad = %s
                    AND a.estado = 'Activo'
                    ORDER BY a.experiencia DESC
                    LIMIT 20
                """, (tenant_id, success_patterns[0]['experiencia'], success_patterns[0]['ciudad']))
                
                recommended_candidates = cursor.fetchall()
            else:
                recommended_candidates = []
            
            return json.dumps({
                "success": True,
                "analysis_type": analysis_type,
                "success_patterns": success_patterns,
                "recommended_candidates": recommended_candidates,
                "insights": {
                    "best_experience_range": success_patterns[0]['experiencia'] if success_patterns else None,
                    "best_city": success_patterns[0]['ciudad'] if success_patterns else None,
                    "average_success_rate": sum([p['tasa_exito'] for p in success_patterns]) / len(success_patterns) if success_patterns else 0
                },
                "tenant_id": tenant_id
            })
            
        elif analysis_type == "vacancy_performance":
            # Análisis de rendimiento de vacantes
            cursor.execute("""
                SELECT 
                    v.cargo_solicitado,
                    c.empresa,
                    COUNT(p.id_postulacion) as total_postulaciones,
                    COUNT(co.id_contratado) as contrataciones,
                    DATEDIFF(CURDATE(), v.fecha_apertura) as dias_abierta,
                    v.estado
                FROM Vacantes v
                JOIN Clientes c ON v.id_cliente = c.id_cliente
                LEFT JOIN Postulaciones p ON v.id_vacante = p.id_vacante
                LEFT JOIN Contratados co ON p.id_afiliado = co.id_afiliado AND p.id_vacante = co.id_vacante
                WHERE v.tenant_id = %s
                GROUP BY v.id_vacante
                ORDER BY total_postulaciones DESC
                LIMIT 15
            """, (tenant_id,))
            
            vacancy_performance = cursor.fetchall()
            
            return json.dumps({
                "success": True,
                "analysis_type": analysis_type,
                "vacancy_performance": vacancy_performance,
                "insights": {
                    "most_popular_positions": [v['cargo_solicitado'] for v in vacancy_performance[:3]],
                    "average_days_to_fill": sum([v['dias_abierta'] for v in vacancy_performance if v['contrataciones'] > 0]) / len([v for v in vacancy_performance if v['contrataciones'] > 0]) if any(v['contrataciones'] > 0 for v in vacancy_performance) else 0
                },
                "tenant_id": tenant_id
            })
            
        else:
            return json.dumps({"error": f"Tipo de análisis '{analysis_type}' no soportado"})
        
    except Exception as e:
        app.logger.error(f"Error en generate_predictive_analytics: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


def manage_clients_intelligent(tenant_id: int, action: str = "get_suggestions", 
                              client_id: int = None, **client_data):
    """
    Gestión inteligente de clientes con sugerencias de candidatos según historial
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        if action == "get_suggestions" and client_id:
            # Obtener historial del cliente
            cursor.execute("""
                SELECT v.cargo_solicitado, COUNT(co.id_contratado) as contrataciones_exitosas
                FROM Vacantes v
                LEFT JOIN Postulaciones p ON v.id_vacante = p.id_vacante
                LEFT JOIN Contratados co ON p.id_afiliado = co.id_afiliado
                WHERE v.id_cliente = %s AND v.tenant_id = %s
                GROUP BY v.cargo_solicitado
                ORDER BY contrataciones_exitosas DESC
                LIMIT 5
            """, (client_id, tenant_id))
            
            client_history = cursor.fetchall()
            
            if client_history:
                # Buscar candidatos similares a los contratados exitosamente
                most_successful_position = client_history[0]['cargo_solicitado']
                
                cursor.execute("""
                    SELECT DISTINCT a.id_afiliado, a.nombre_completo, a.experiencia, a.ciudad, a.email
                    FROM Afiliados a
                    JOIN Postulaciones p ON a.id_afiliado = p.id_afiliado
                    JOIN Vacantes v ON p.id_vacante = v.id_vacante
                    JOIN Contratados co ON a.id_afiliado = co.id_afiliado
                    WHERE v.cargo_solicitado LIKE %s 
                    AND a.tenant_id = %s
                    AND a.estado = 'Activo'
                    ORDER BY a.experiencia DESC
                    LIMIT 10
                """, (f"%{most_successful_position}%", tenant_id))
                
                suggested_candidates = cursor.fetchall()
            else:
                suggested_candidates = []
            
            # Obtener información del cliente
            cursor.execute("""
                SELECT empresa, contacto_nombre, email, telefono
                FROM Clientes 
                WHERE id_cliente = %s AND tenant_id = %s
            """, (client_id, tenant_id))
            
            client_info = cursor.fetchone()
            
            return json.dumps({
                "success": True,
                "client_info": client_info,
                "client_history": client_history,
                "suggested_candidates": suggested_candidates,
                "insights": {
                    "most_successful_position": client_history[0]['cargo_solicitado'] if client_history else None,
                    "total_hires": sum([h['contrataciones_exitosas'] for h in client_history]),
                    "position_diversity": len(client_history)
                },
                "tenant_id": tenant_id
            })
            
        elif action == "client_stats":
            # Estadísticas generales de clientes
            cursor.execute("""
                SELECT 
                    c.id_cliente,
                    c.empresa,
                    COUNT(DISTINCT v.id_vacante) as total_vacantes,
                    COUNT(DISTINCT co.id_contratado) as total_contrataciones,
                    MAX(v.fecha_apertura) as ultima_vacante
                FROM Clientes c
                LEFT JOIN Vacantes v ON c.id_cliente = v.id_cliente
                LEFT JOIN Postulaciones p ON v.id_vacante = p.id_vacante
                LEFT JOIN Contratados co ON p.id_afiliado = co.id_afiliado
                WHERE c.tenant_id = %s
                GROUP BY c.id_cliente
                ORDER BY total_contrataciones DESC
                LIMIT 10
            """, (tenant_id,))
            
            client_stats = cursor.fetchall()
            
            return json.dumps({
                "success": True,
                "client_stats": client_stats,
                "tenant_id": tenant_id
            })
            
        else:
            return json.dumps({"error": f"Acción '{action}' no soportada"})
        
    except Exception as e:
        app.logger.error(f"Error en manage_clients_intelligent: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


def schedule_interviews_intelligent(tenant_id: int, postulation_id: int, 
                                  interview_date: str, interview_time: str, 
                                  interviewer: str, notes: str = ""):
    """
    Programación inteligente de entrevistas con validación multi-tenant
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Verificar que la postulación pertenece al tenant
        cursor.execute("""
            SELECT p.id_postulacion, p.id_afiliado, p.id_vacante, 
                   a.nombre_completo, a.telefono, a.email,
                   v.cargo_solicitado, c.empresa
            FROM Postulaciones p
            JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            JOIN Clientes c ON v.id_cliente = c.id_cliente
            WHERE p.id_postulacion = %s AND v.tenant_id = %s
        """, (postulation_id, tenant_id))
        
        postulation_info = cursor.fetchone()
        if not postulation_info:
            return json.dumps({
                "error": "Postulación no encontrada o no pertenece a su organización"
            })
        
        # Verificar conflictos de horario (opcional - básico)
        cursor.execute("""
            SELECT COUNT(*) as conflictos
            FROM Entrevistas e
            JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE v.tenant_id = %s 
            AND e.fecha_entrevista = %s 
            AND e.hora_entrevista = %s
            AND e.entrevistador = %s
        """, (tenant_id, interview_date, interview_time, interviewer))
        
        conflicts = cursor.fetchone()['conflictos']
        
        # Crear la entrevista
        cursor.execute("""
            INSERT INTO Entrevistas (id_postulacion, fecha_entrevista, hora_entrevista, 
                                   entrevistador, notas, estado, created_at)
            VALUES (%s, %s, %s, %s, %s, 'Programada', NOW())
        """, (postulation_id, interview_date, interview_time, interviewer, notes))
        
        interview_id = cursor.lastrowid
        
        # Actualizar estado de la postulación
        cursor.execute("""
            UPDATE Postulaciones 
            SET estado = 'Entrevista Programada' 
            WHERE id_postulacion = %s
        """, (postulation_id,))
        
        conn.commit()
        
        return json.dumps({
            "success": True,
            "interview_id": interview_id,
            "candidate_info": {
                "name": postulation_info['nombre_completo'],
                "email": postulation_info['email'],
                "phone": postulation_info['telefono']
            },
            "interview_details": {
                "date": interview_date,
                "time": interview_time,
                "interviewer": interviewer,
                "position": postulation_info['cargo_solicitado'],
                "company": postulation_info['empresa']
            },
            "conflicts_detected": conflicts > 0,
            "message": f"Entrevista programada para {postulation_info['nombre_completo']} el {interview_date} a las {interview_time}",
            "tenant_id": tenant_id
        })
        
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error en schedule_interviews_intelligent: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


def get_smart_recommendations(tenant_id: int, context: str = "vacancy_candidates", 
                             vacancy_id: int = None, candidate_id: int = None, **params):
    """
    Sistema de recomendaciones inteligentes (solo cuando el usuario las pida)
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        if context == "vacancy_candidates" and vacancy_id:
            # Recomendar candidatos ideales para una vacante específica
            cursor.execute("""
                SELECT v.cargo_solicitado, v.requisitos, c.empresa
                FROM Vacantes v
                JOIN Clientes c ON v.id_cliente = c.id_cliente
                WHERE v.id_vacante = %s AND v.tenant_id = %s
            """, (vacancy_id, tenant_id))
            
            vacancy_info = cursor.fetchone()
            if not vacancy_info:
                return json.dumps({"error": "Vacante no encontrada"})
            
            # Buscar candidatos con experiencia similar
            cursor.execute("""
                SELECT a.id_afiliado, a.nombre_completo, a.experiencia, a.ciudad, 
                       a.email, a.telefono, a.fecha_registro,
                       COUNT(co.id_contratado) as contrataciones_previas
                FROM Afiliados a
                LEFT JOIN Contratados co ON a.id_afiliado = co.id_afiliado
                WHERE a.tenant_id = %s 
                AND a.estado = 'Activo'
                AND (a.experiencia_detalle LIKE %s OR a.habilidades LIKE %s)
                GROUP BY a.id_afiliado
                ORDER BY a.experiencia DESC, contrataciones_previas DESC
                LIMIT 15
            """, (tenant_id, f"%{vacancy_info['cargo_solicitado']}%", f"%{vacancy_info['cargo_solicitado']}%"))
            
            recommended_candidates = cursor.fetchall()
            
            # Calcular score de compatibilidad básico
            for candidate in recommended_candidates:
                score = 50  # Base score
                if candidate['experiencia'] >= 3:
                    score += 20
                if candidate['contrataciones_previas'] > 0:
                    score += 15
                # Agregar más criterios según sea necesario
                candidate['compatibility_score'] = min(score, 100)
            
            return json.dumps({
                "success": True,
                "context": context,
                "vacancy_info": vacancy_info,
                "recommended_candidates": sorted(recommended_candidates, 
                                               key=lambda x: x['compatibility_score'], 
                                               reverse=True),
                "total_recommendations": len(recommended_candidates),
                "tenant_id": tenant_id
            })
            
        elif context == "candidate_vacancies" and candidate_id:
            # Recomendar vacantes para un candidato específico
            cursor.execute("""
                SELECT a.experiencia, a.ciudad, a.habilidades
                FROM Afiliados a
                WHERE a.id_afiliado = %s AND a.tenant_id = %s
            """, (candidate_id, tenant_id))
            
            candidate_info = cursor.fetchone()
            if not candidate_info:
                return json.dumps({"error": "Candidato no encontrado"})
            
            cursor.execute("""
                SELECT v.id_vacante, v.cargo_solicitado, v.ciudad, v.salario, 
                       v.requisitos, c.empresa, v.fecha_apertura
                FROM Vacantes v
                JOIN Clientes c ON v.id_cliente = c.id_cliente
                WHERE v.tenant_id = %s 
                AND v.estado = 'Abierta'
                AND v.ciudad = %s
                ORDER BY v.fecha_apertura DESC
                LIMIT 10
            """, (tenant_id, candidate_info['ciudad']))
            
            matching_vacancies = cursor.fetchall()
            
            return json.dumps({
                "success": True,
                "context": context,
                "candidate_info": candidate_info,
                "matching_vacancies": matching_vacancies,
                "total_matches": len(matching_vacancies),
                "tenant_id": tenant_id
            })
            
        else:
            return json.dumps({"error": f"Contexto '{context}' no soportado o faltan parámetros"})
        
    except Exception as e:
        app.logger.error(f"Error en get_smart_recommendations: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


# ===============================================================
# 🔗 HERRAMIENTAS DE FASE 3: INTEGRACIONES PREMIUM
# ===============================================================

def advanced_integrations(tenant_id: int, integration_type: str, action: str = "search", **data):
    """
    Integraciones premium con servicios externos
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "Error de conexión a BD"})
    
    cursor = conn.cursor(dictionary=True)
    try:
        if integration_type == "linkedin_search":
            # Simulación de búsqueda en LinkedIn (requiere LinkedIn API real)
            search_term = data.get('search_term', '')
            location = data.get('location', '')
            
            # Por ahora, buscar candidatos similares en nuestra BD y sugerir búsqueda en LinkedIn
            cursor.execute("""
                SELECT a.nombre_completo, a.experiencia, a.ciudad, a.habilidades
                FROM Afiliados a
                WHERE a.tenant_id = %s 
                AND (a.nombre_completo LIKE %s OR a.habilidades LIKE %s)
                AND a.ciudad LIKE %s
                LIMIT 10
            """, (tenant_id, f"%{search_term}%", f"%{search_term}%", f"%{location}%"))
            
            existing_candidates = cursor.fetchall()
            
            return json.dumps({
                "success": True,
                "integration_type": "linkedin_search",
                "search_term": search_term,
                "location": location,
                "existing_candidates": existing_candidates,
                "linkedin_suggestion": f"Buscar en LinkedIn: '{search_term}' en {location}",
                "message": f"Encontré {len(existing_candidates)} candidatos similares en tu base de datos. Para buscar en LinkedIn, necesitas configurar la integración con LinkedIn API.",
                "setup_required": "LinkedIn API credentials needed",
                "tenant_id": tenant_id
            })
            
        elif integration_type == "google_calendar":
            # Integración con Google Calendar para programar entrevistas
            interview_date = data.get('interview_date')
            interview_time = data.get('interview_time')
            candidate_name = data.get('candidate_name')
            interviewer_email = data.get('interviewer_email')
            
            if action == "create_event":
                # Simulación de creación de evento en Google Calendar
                event_details = {
                    "title": f"Entrevista con {candidate_name}",
                    "date": interview_date,
                    "time": interview_time,
                    "attendees": [interviewer_email],
                    "description": f"Entrevista de trabajo con {candidate_name}"
                }
                
                return json.dumps({
                    "success": True,
                    "integration_type": "google_calendar",
                    "action": "create_event",
                    "event_details": event_details,
                    "message": f"Evento de calendario creado para entrevista con {candidate_name}",
                    "setup_required": "Google Calendar API credentials needed",
                    "tenant_id": tenant_id
                })
                
        elif integration_type == "job_boards":
            # Integración con bolsas de trabajo para publicar vacantes
            vacancy_id = data.get('vacancy_id')
            job_boards = data.get('job_boards', ['indeed', 'linkedin_jobs', 'glassdoor'])
            
            if vacancy_id:
                # Obtener detalles de la vacante
                cursor.execute("""
                    SELECT v.cargo_solicitado, v.ciudad, v.salario, v.requisitos, c.empresa
                    FROM Vacantes v
                    JOIN Clientes c ON v.id_cliente = c.id_cliente
                    WHERE v.id_vacante = %s AND v.tenant_id = %s
                """, (vacancy_id, tenant_id))
                
                vacancy_info = cursor.fetchone()
                
                if vacancy_info:
                    job_posting = {
                        "title": vacancy_info['cargo_solicitado'],
                        "company": vacancy_info['empresa'],
                        "location": vacancy_info['ciudad'],
                        "salary": vacancy_info['salario'],
                        "requirements": vacancy_info['requisitos'],
                        "target_boards": job_boards
                    }
                    
                    return json.dumps({
                        "success": True,
                        "integration_type": "job_boards",
                        "vacancy_id": vacancy_id,
                        "job_posting": job_posting,
                        "target_boards": job_boards,
                        "message": f"Vacante '{vacancy_info['cargo_solicitado']}' lista para publicar en {len(job_boards)} bolsas de trabajo",
                        "setup_required": "Job board API credentials needed",
                        "tenant_id": tenant_id
                    })
                else:
                    return json.dumps({"error": "Vacante no encontrada"})
                    
        elif integration_type == "slack_notifications":
            # Integración con Slack para notificaciones internas
            message = data.get('message', '')
            channel = data.get('channel', '#reclutamiento')
            event_type = data.get('event_type', 'general')
            
            notification_data = {
                "channel": channel,
                "message": message,
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "tenant_id": tenant_id
            }
            
            return json.dumps({
                "success": True,
                "integration_type": "slack_notifications",
                "notification_data": notification_data,
                "message": f"Notificación enviada a Slack canal {channel}",
                "setup_required": "Slack webhook URL needed",
                "tenant_id": tenant_id
            })
            
        elif integration_type == "ats_sync":
            # Sincronización con sistemas ATS externos
            ats_system = data.get('ats_system', 'workday')
            sync_type = data.get('sync_type', 'candidates')
            
            if sync_type == "candidates":
                # Obtener candidatos para sincronizar
                cursor.execute("""
                    SELECT a.id_afiliado, a.nombre_completo, a.email, a.telefono, 
                           a.experiencia, a.ciudad, a.fecha_registro
                    FROM Afiliados a
                    WHERE a.tenant_id = %s 
                    AND a.fecha_registro >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    LIMIT 50
                """, (tenant_id,))
                
                recent_candidates = cursor.fetchall()
                
                # Convertir fechas para JSON
                for candidate in recent_candidates:
                    if candidate.get('fecha_registro'):
                        candidate['fecha_registro'] = candidate['fecha_registro'].isoformat()
                
                return json.dumps({
                    "success": True,
                    "integration_type": "ats_sync",
                    "ats_system": ats_system,
                    "sync_type": sync_type,
                    "candidates_to_sync": recent_candidates,
                    "total_candidates": len(recent_candidates),
                    "message": f"Preparados {len(recent_candidates)} candidatos para sincronizar con {ats_system}",
                    "setup_required": f"{ats_system} API credentials needed",
                    "tenant_id": tenant_id
                })
                
        else:
            return json.dumps({"error": f"Tipo de integración '{integration_type}' no soportado"})
        
    except Exception as e:
        app.logger.error(f"Error en advanced_integrations: {str(e)}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()


def export_data_multi_tenant(tenant_id: int, export_type: str = "candidates", 
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

#     data = request.get_json()
#     user_prompt = data.get('prompt')
#     history = data.get('history', [])
#     
#     if not user_prompt:
#         return jsonify({"error": "Prompt es requerido"}), 400
# 
#     try:
#         messages = [
#             {"role": "system", "content": """
#                 Eres un asistente de reclutamiento experto para la agencia Henmir. Tu personalidad es proactiva, eficiente y directa.
#                 REGLAS CRÍTICAS:
#                 1.  Uso de Herramientas: Tu función principal es ejecutar acciones usando las herramientas proporcionadas. Para cualquier acción que implique buscar, postular, agendar o actualizar datos, DEBES usar una herramienta. NO inventes información.
#                 2.  Contexto: Presta mucha atención al historial de la conversación para entender órdenes de seguimiento como "postula al segundo candidato" o "usa el mismo mensaje".
#                 3.  Clarificación: Si una orden es ambigua (ej. "postula a Juan a la vacante de ventas" y hay varias vacantes de ventas), DEBES hacer una pregunta para clarificar antes de usar una herramienta.
#                 4.  Identificadores: Para acciones sobre candidatos o vacantes, prioriza siempre el uso de IDs numéricos si están disponibles en el historial. Si no, usa nombres o números de identidad para buscarlos.
#                 """
#             }
#         ]
#         for item in history:
#             if item.get('user'): messages.append({"role": "user", "content": item.get('user')})
#             if item.get('assistant'): messages.append({"role": "assistant", "content": item.get('assistant')})
#         messages.append({"role": "user", "content": user_prompt})
# 
#         tools = [
#             {"type": "function", "function": {"name": "search_candidates_tool", "description": "Busca candidatos.", "parameters": {"type": "object", "properties": {"term": {"type": "string"}, "tags": {"type": "string"}, "experience": {"type": "string"}, "city": {"type": "string"}, "recency_days": {"type": "integer"}}, "required": []}}},
#             # --- ✨ NUEVA HERRAMIENTA AÑADIDA AQUÍ ✨ ---
#             {"type": "function", "function": {"name": "get_active_vacancies_details_tool", "description": "Obtiene una lista detallada de vacantes activas, incluyendo requisitos, ciudad y salario. Útil para cuando el reclutador quiere ver las opciones disponibles.", "parameters": {"type": "object", "properties": {"city": {"type": "string", "description": "Opcional. La ciudad para filtrar."}, "keyword": {"type": "string", "description": "Opcional. Palabra clave para buscar en el cargo o requisitos."}}, "required": []}}},
#             {"type": "function", "function": {"name": "postulate_candidate_to_vacancy", "description": "Postula un candidato a una vacante usando su ID interno o su número de identidad.", "parameters": {"type": "object", "properties": {"vacancy_id": {"type": "integer"}, "candidate_id": {"type": "integer"}, "identity_number": {"type": "string"}, "comments": {"type": "string"}}, "required": ["vacancy_id"]}}},
#             {"type": "function", "function": {"name": "prepare_whatsapp_campaign_tool", "description": "Prepara una campaña de WhatsApp. Usa el mensaje si el usuario lo provee; si no, usa una plantilla.", "parameters": {"type": "object", "properties": {"message_body": {"type": "string", "description": "Opcional. El cuerpo del mensaje a enviar."}, "template_id": {"type": "integer", "description": "Opcional. El ID de la plantilla de mensaje a usar."}, "candidate_ids": {"type": "string", "description": "Opcional. IDs o identidades de candidatos, separados por comas."}, "vacancy_id": {"type": "integer", "description": "Opcional. Filtra candidatos por ID de vacante."}}, "required": []}}},
#             {"type": "function", "function": {"name": "schedule_interview_tool", "description": "Agenda una nueva entrevista.", "parameters": {"type": "object", "properties": {"postulation_id": {"type": "integer"}, "interview_date": {"type": "string"}, "interview_time": {"type": "string"}, "interviewer": {"type": "string"}, "notes": {"type": "string"}}, "required": ["postulation_id", "interview_date", "interview_time", "interviewer"]}}},
#             {"type": "function", "function": {"name": "update_application_status_tool", "description": "Actualiza el estado de una postulación.", "parameters": {"type": "object", "properties": {"postulation_id": {"type": "integer"}, "new_status": {"type": "string"}}, "required": ["postulation_id", "new_status"]}}},
#             {"type": "function", "function": {"name": "get_report_data_tool", "description": "Obtiene los datos de un reporte interno.", "parameters": {"type": "object", "properties": {"report_name": {"type": "string"}},"required": ["report_name"]}}},
#             {"type": "function", "function": {"name": "get_vacancy_id_by_name_tool", "description": "Busca el ID numérico de una vacante por su nombre.", "parameters": {"type": "object", "properties": {"vacancy_name": {"type": "string"}, "company_name": {"type": "string"}},"required": ["vacancy_name"]}}}
#         ]
#         
#         response = openai_client.chat.completions.create(
#             model="gpt-4o", messages=messages, tools=tools, tool_choice="auto"
#         )
#         response_message = response.choices[0].message
#         tool_calls = response_message.tool_calls
# 
#         if tool_calls:
#             available_functions = {
#                 "search_candidates_tool": search_candidates_tool,
#                 "postulate_candidate_to_vacancy": postulate_candidate_to_vacancy,
#                 "prepare_whatsapp_campaign_tool": prepare_whatsapp_campaign_tool,
#                 "schedule_interview_tool": schedule_interview_tool,
#                 "update_application_status_tool": update_application_status_tool,
#                 "get_report_data_tool": get_report_data_tool,
#                 "get_vacancy_id_by_name_tool": get_vacancy_id_by_name_tool,
#                 # --- ✨ NUEVA FUNCIÓN AÑADIDA AL DICCIONARIO ✨ ---
#                 "get_active_vacancies_details_tool": get_active_vacancies_details_tool,
#             }
#             messages.append(response_message)
#             last_function_response = None
#             last_function_name = ""
#             for tool_call in tool_calls:
#                 function_name = tool_call.function.name
#                 function_args = json.loads(tool_call.function.arguments)
#                 function_to_call = available_functions.get(function_name)
#                 if function_to_call:
#                     function_response = function_to_call(**function_args)
#                     last_function_response = function_response
#                     last_function_name = function_name
#                 else:
#                     function_response = json.dumps({"error": f"Función '{function_name}' no encontrada."})
#                 messages.append({
#                     "tool_call_id": tool_call.id, "role": "tool", "name": function_name,
#                     "content": function_response if isinstance(function_response, str) else json.dumps(function_response),
#                 })
#             final_response_message = openai_client.chat.completions.create(
#                 model="gpt-4o", messages=messages
#             ).choices[0].message.content
#             if last_function_name == 'prepare_whatsapp_campaign_tool':
#                 campaign_data = json.loads(last_function_response)
#                 if campaign_data.get("data"):
#                     return jsonify({"type": "whatsapp_campaign_prepared", "text_response": final_response_message, "campaign_data": campaign_data["data"]})
#             return jsonify({"type": "text_response", "data": final_response_message})
#         else:
#             return jsonify({"type": "text_response", "data": response_message.content})
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return jsonify({"error": str(e)}), 500
    



# OLD BOT TOOL REMOVED - Will be replaced with multi-tenant version
# def prepare_whatsapp_campaign_tool(message_body: str, candidate_id: int = None, identity_number: str = None, candidate_ids: str = None, vacancy_id: int = None, application_date: str = None):
    """
    Prepara una campaña de WhatsApp. Busca candidatos y devuelve su info de contacto junto con el mensaje.
    Puede buscar por ID/identidad de candidato DIRECTAMENTE, por una lista de IDs, o filtrar postulantes por vacante.
    """
    conn = get_db_connection()
    if not conn: return json.dumps({"error": "DB connection failed"})
    cursor = conn.cursor(dictionary=True)
    
    try:
        final_message_body = message_body
        if not final_message_body:
            # Si la IA no extrajo un mensaje, buscamos la plantilla 1 por defecto (o la que prefieras)
            cursor.execute("SELECT cuerpo_mensaje FROM Whatsapp_Templates WHERE id_template = 1")
            template = cursor.fetchone()
            final_message_body = template['cuerpo_mensaje'] if template else "Hola [name], te contactamos de Henmir."

        candidates = []
        # ✨ LÓGICA DE BÚSQUEDA CORREGIDA Y SIMPLIFICADA ✨
        # Prioridad 1: Si se da un ID o identidad individual.
        if candidate_id or identity_number:
            target_id = _get_candidate_id(conn, candidate_id, identity_number)
            if target_id:
                cursor.execute("SELECT id_afiliado, nombre_completo, telefono FROM Afiliados WHERE id_afiliado = %s", (target_id,))
                candidates = cursor.fetchall()
        # Prioridad 2: Si se da una lista de IDs/identidades.
        elif candidate_ids:
            id_list = re.findall(r'\b\d+\b', candidate_ids) # Buscamos cualquier número
            if id_list:
                placeholders = ','.join(['%s'] * len(id_list))
                sql = f"SELECT id_afiliado, nombre_completo, telefono FROM Afiliados WHERE id_afiliado IN ({placeholders}) OR identidad IN ({placeholders})"
                cursor.execute(sql, id_list * 2)
                candidates = cursor.fetchall()
        # Prioridad 3: Si no, filtramos por vacante.
        elif vacancy_id:
            # Lógica para filtrar por vacante (sin cambios)
            pass

        if not candidates:
            return json.dumps({"data": {"candidates": [], "message": ""}, "message": "No se encontraron candidatos con esos criterios."})

        recipients = []
        for cand in candidates:
            clean_phone = clean_phone_number(cand.get('telefono'))
            if clean_phone:
                recipients.append({"nombre_completo": cand['nombre_completo'], "telefono": clean_phone})
        
        return json.dumps({"data": {"recipients": recipients, "message_body": final_message_body}, "message": f"He preparado una campaña para {len(recipients)} candidato(s) validados."})

    finally:
        cursor.close()
        conn.close()

    

# OLD BOT TOOL REMOVED - Will be replaced with multi-tenant version  
# def schedule_interview_tool(postulation_id: int, interview_date: str, interview_time: str, interviewer: str, notes: str = ""):
    """
    Agenda una nueva entrevista para una postulación existente.
    'interview_date' debe estar en formato YYYY-MM-DD.
    'interview_time' debe estar en formato HH:MM:SS (24 horas).
    """
    conn = get_db_connection()
    if not conn: 
        return json.dumps({"success": False, "error": "Fallo en la conexión a la BD."})

    cursor = conn.cursor()
    try:
        # Combinamos la fecha y la hora para el formato DATETIME de la base de datos
        datetime_str = f"{interview_date} {interview_time}"

        # Insertamos la nueva entrevista
        sql_insert = "INSERT INTO Entrevistas (id_postulacion, fecha_hora, entrevistador, resultado, observaciones) VALUES (%s, %s, %s, 'Programada', %s)"
        cursor.execute(sql_insert, (postulation_id, datetime_str, interviewer, notes))

        # Actualizamos el estado de la postulación a 'En Entrevista'
        sql_update = "UPDATE Postulaciones SET estado = 'En Entrevista' WHERE id_postulacion = %s"
        cursor.execute(sql_update, (postulation_id,))

        conn.commit()
        return json.dumps({"success": True, "message": f"Entrevista agendada exitosamente para la postulación {postulation_id}."})

    except mysql.connector.Error as err:
        conn.rollback()
        # Error común: la postulación no existe.
        if err.errno == 1452:
            return json.dumps({"success": False, "error": f"No se pudo agendar. La postulación con ID {postulation_id} no existe."})
        return json.dumps({"success": False, "error": f"Error de base de datos: {str(err)}"})
    except Exception as e:
        conn.rollback()
        return json.dumps({"success": False, "error": f"Error inesperado: {str(e)}"})
    finally:
        cursor.close()
        conn.close()



def update_application_status_tool(postulation_id: int, new_status: str):
    """
    Actualiza el estado de una postulación existente.
    Los estados válidos son: 'Recibida', 'En Revisión', 'Pre-seleccionado', 'En Entrevista', 'Oferta', 'Contratado', 'Rechazado'.
    """
    valid_statuses = ['Recibida', 'En Revisión', 'Pre-seleccionado', 'En Entrevista', 'Oferta', 'Contratado', 'Rechazado']
    if new_status not in valid_statuses:
        return json.dumps({"success": False, "error": f"'{new_status}' no es un estado válido. Los estados permitidos son: {', '.join(valid_statuses)}"})

    conn = get_db_connection()
    if not conn: 
        return json.dumps({"success": False, "error": "Fallo en la conexión a la BD."})

    cursor = conn.cursor()
    try:
        sql = "UPDATE Postulaciones SET estado = %s WHERE id_postulacion = %s"
        cursor.execute(sql, (new_status, postulation_id))

        if cursor.rowcount == 0:
            conn.rollback()
            return json.dumps({"success": False, "error": f"No se encontró una postulación con el ID {postulation_id}."})

        conn.commit()
        return json.dumps({"success": True, "message": f"El estado de la postulación {postulation_id} se ha actualizado a '{new_status}'."})

    except Exception as e:
        conn.rollback()
        return json.dumps({"success": False, "error": f"Error inesperado al actualizar el estado: {str(e)}"})
    finally:
        cursor.close()
        conn.close()



def get_report_data_tool(report_name: str):
    """
    Obtiene los datos de un reporte específico del sistema para poder analizarlos o resumirlos.
    'report_name' debe ser uno de los IDs de reporte válidos, como 'vacantes_activas' o 'pagos_pendientes'.
    """
    # --- Esta función simula una llamada a nuestra propia API de reportes ---
    # No podemos usar requests.get aquí fácilmente en un entorno de desarrollo de Flask,
    # así que replicamos la lógica de la función get_reports.

    if not report_name:
        return json.dumps({"error": "Se requiere el nombre del reporte"})

    conn = get_db_connection()
    if not conn: 
        return json.dumps({"error": "DB connection failed"})

    cursor = conn.cursor(dictionary=True)
    sql = "" # Dejaremos esto vacío ya que la lógica está en get_reports

    try:
        # Reutilizamos la lógica de la función get_reports para no repetir código
        # (En una app más grande, esto se refactorizaría a una función interna común)

        # --- Aquí pegamos la lógica de la función get_reports ---
        # Para mantener la simplicidad, por ahora solo implementaremos la llamada para dos reportes clave.
        # El asistente aprenderá el patrón.
        if report_name == 'vacantes_activas':
            sql = """
                SELECT v.cargo_solicitado, c.empresa, 
                       (SELECT COUNT(*) FROM Postulaciones p WHERE p.id_vacante = v.id_vacante) as total_postulaciones
                FROM Vacantes v JOIN Clientes c ON v.id_cliente = c.id_cliente
                WHERE v.estado = 'Abierta' ORDER BY total_postulaciones DESC;
            """
        elif report_name == 'pagos_pendientes':
            sql = """
                SELECT c.empresa, v.cargo_solicitado, (co.tarifa_servicio - co.monto_pagado) AS saldo_pendiente
                FROM Contratados co
                JOIN Vacantes v ON co.id_vacante = v.id_vacante
                JOIN Clientes c ON v.id_cliente = c.id_cliente
                WHERE (co.tarifa_servicio - co.monto_pagado) > 0 ORDER BY saldo_pendiente DESC;
            """
        else:
             return json.dumps({"error": f"El reporte '{report_name}' no es soportado por el asistente en este momento."})

        cursor.execute(sql)
        results = cursor.fetchall()

        # Convertimos a JSON compatible
        for row in results:
            for key, value in row.items():
                if isinstance(value, (datetime, date)):
                    row[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    row[key] = float(value)

        # Limitamos la cantidad de datos para no sobrecargar al modelo
        if len(results) > 15:
            summary = {"summary": f"Se encontraron {len(results)} registros. Mostrando los primeros 15.", "data": results[:15]}
            return json.dumps(summary)

        return json.dumps(results)

    except Exception as e:
        return json.dumps({"error": f"Error al generar data para el reporte: {str(e)}"})
    finally:
        cursor.close()
        conn.close()



def get_vacancy_id_by_name_tool(vacancy_name: str, company_name: str = None):
    """
    Busca el ID numérico de una vacante a partir de su nombre y, opcionalmente, el nombre de la empresa.
    Esencial para cuando el usuario pide postular a alguien a una vacante por nombre en lugar de por ID.
    """
    conn = get_db_connection()
    if not conn: return json.dumps({"error": "DB connection failed"})
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT v.id_vacante FROM Vacantes v"
        params = []
        conditions = []

        conditions.append("v.cargo_solicitado LIKE %s")
        params.append(f"%{vacancy_name}%")

        if company_name:
            query += " JOIN Clientes c ON v.id_cliente = c.id_cliente"
            conditions.append("c.empresa LIKE %s")
            params.append(f"%{company_name}%")
        
        query += " WHERE " + " AND ".join(conditions) + " LIMIT 1"
        
        cursor.execute(query, tuple(params))
        result = cursor.fetchone()
        
        if result:
            return json.dumps(result)
        else:
            return json.dumps({"error": "No se encontró una vacante que coincida con esos criterios."})
    finally:
        cursor.close()
        conn.close()
        
# --- ✨ NUEVA FUNCIÓN-HERRAMIENTA PARA EL ASISTENTE INTERNO ✨ ---
def get_active_vacancies_details_tool(city: str = None, keyword: str = None):
    """
    Busca vacantes activas y devuelve sus detalles completos, incluyendo cargo,
    empresa, ciudad, salario y requisitos. Ideal para que el reclutador evalúe las vacantes.
    """
    conn = get_db_connection()
    if not conn: return json.dumps({"error": "DB connection failed"})
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT v.id_vacante, v.cargo_solicitado, c.empresa, v.ciudad, v.salario, v.requisitos
            FROM Vacantes v JOIN Clientes c ON v.id_cliente = c.id_cliente
            WHERE v.estado = 'Abierta'
        """
        params = []
        if city:
            query += " AND v.ciudad LIKE %s"
            params.append(f"%{city}%")
        if keyword:
            query += " AND (v.cargo_solicitado LIKE %s OR v.requisitos LIKE %s)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        # Convertir Decimal a float para que sea serializable a JSON
        for row in results:
            if isinstance(row.get('salario'), Decimal):
                row['salario'] = float(row['salario'])
        return json.dumps(results)
    finally:
        cursor.close()
        conn.close()



# ===============================================================
# SECCIÓN 1.5: HERRAMIENTAS ADICIONALES (PARA CHATBOT EXTERNO)
# ===============================================================


def search_vacancies_tool(city: str = None, keyword: str = None):
    """
    (Herramienta para el bot de WhatsApp) Busca TODAS las vacantes disponibles.
    Devuelve solo información pública (cargo, ciudad), nunca datos sensibles.
    """
    app.logger.info(f"[Herramienta Chatbot] Buscando TODAS las vacantes: ciudad='{city}', keyword='{keyword}'")
    conn = get_db_connection()
    if not conn: 
        app.logger.error("Error de conexión a BD en search_vacancies_tool")
        return json.dumps({"error": "DB connection failed"})
    cursor = conn.cursor(dictionary=True)
    
    try:
        # ✨ CAMBIO: Consulta sin ningún LIMIT.
        query = "SELECT cargo_solicitado, ciudad FROM Vacantes WHERE estado = 'Abierta'"
        params = []
        
        if city:
            # Usamos LOWER() para hacer la búsqueda insensible a mayúsculas/minúsculas
            query += " AND LOWER(ciudad) LIKE LOWER(%s)"
            params.append(f"%{city}%")
        
        if keyword:
            # Hacemos la búsqueda de palabra clave también insensible a mayúsculas/minúsculas
            query += " AND (LOWER(cargo_solicitado) LIKE LOWER(%s) OR LOWER(requisitos) LIKE LOWER(%s))"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
            
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        
        app.logger.info(f"Encontradas {len(results)} vacantes en la base de datos")
        return json.dumps(results)
        
    except Exception as e:
        app.logger.error(f"Error en search_vacancies_tool: {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

#
# NOTA: No necesitamos añadir 'bot_validate_registration' aquí porque
# ya tenemos la ruta /api/bot_tools/validate_registration que hace esa función.
# Llamar a una ruta desde el bot es más limpio. 
# Si decidiéramos unificarlo, lo haríamos, pero por ahora la ruta dedicada es suficiente.
#



# ===============================================================
# SECCIÓN 2: WEBHOOK Y GESTIÓN DE DATOS MASIVOS
# ===============================================================

@app.route('/api/webhook/new-candidate-jsonp', methods=['GET'])
def webhook_new_candidate_jsonp():
    callback_function = request.args.get('callback', 'callback')
    api_key = request.args.get('apiKey')
    if not api_key or api_key != os.getenv('WEBHOOK_API_KEY'):
        error_payload = json.dumps({"success": False, "error": "Acceso no autorizado"})
        return Response(f"{callback_function}({error_payload})", mimetype='application/javascript')
    conn = get_db_connection()
    if not conn:
        error_payload = json.dumps({"success": False, "error": "Error de conexión a la BD"})
        return Response(f"{callback_function}({error_payload})", mimetype='application/javascript')
    cursor = conn.cursor()
    try:
        record = request.args
        identidad = str(record.get('identidad', '')).replace('-', '').strip()
        if not identidad: raise ValueError("El número de identidad es obligatorio.")

        # --- CAMBIO CLAVE AQUÍ ---
        # Si el email viene vacío o no existe, lo convertimos a None (que se traduce en NULL en SQL)
        email = record.get('email') or None

        rotativos = 1 if str(record.get('disponibilidad_rotativos')).strip().lower() == 'si' else 0
        transporte = 1 if str(record.get('transporte_propio')).strip().lower() == 'si' else 0
        
        sql_upsert = """
            INSERT INTO Afiliados (fecha_registro, nombre_completo, identidad, telefono, email, experiencia, ciudad, grado_academico, cv_url, observaciones, contrato_url, disponibilidad_rotativos, transporte_propio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                nombre_completo=VALUES(nombre_completo), telefono=VALUES(telefono), email=VALUES(email),
                experiencia=VALUES(experiencia), ciudad=VALUES(ciudad), grado_academico=VALUES(grado_academico),
                cv_url=VALUES(cv_url), observaciones=VALUES(observaciones), contrato_url=VALUES(contrato_url),
                disponibilidad_rotativos=VALUES(disponibilidad_rotativos), transporte_propio=VALUES(transporte_propio);
        """

        # REEMPLAZA LAS DOS LÍNEAS DE data_tuple Y cursor.execute CON ESTE BLOQUE COMPLETO

        # Como Google Forms no envía la fecha, generamos la fecha y hora actual AHORA.
        fecha_de_registro_actual = datetime.now()

        # Construimos la tupla de datos usando nuestra nueva variable de fecha.
        data_tuple = (
            fecha_de_registro_actual, 
            record.get('nombre_completo'), 
            identidad,
            record.get('telefono'), 
            email,
            record.get('experiencia'),
            record.get('ciudad'), 
            record.get('grado_academico'), 
            record.get('cv_url'),
            record.get('observaciones'), 
            record.get('contrato_url'), 
            rotativos, 
            transporte
        )
        
        # Ejecutamos la consulta SQL con la tupla que AHORA SÍ contiene una fecha válida.
        cursor.execute(sql_upsert, data_tuple)
        
        # Ejecutamos la consulta
        cursor.execute(sql_upsert, data_tuple)
        
        conn.commit()
        success_payload = json.dumps({"success": True, "message": "Candidato sincronizado vía JSONP."})
        return Response(f"{callback_function}({success_payload})", mimetype='application/javascript')
    except Exception as e:
        conn.rollback()
        error_payload = json.dumps({"success": False, "error": str(e)})
        return Response(f"{callback_function}({error_payload})", mimetype='application/javascript')
    finally:
        cursor.close()
        conn.close()

@app.route('/api/download-template', methods=['GET'])
@token_required
def download_template():
    data_type = request.args.get('type', 'afiliados')
    TEMPLATE_HEADERS = {
        'afiliados': [
            'Marca temporal', 'Contrato(respuesta de si y no )', 'Nombre completo:', 'No. de identidad Sin Guiones',
            'Numero de telefono', 'Dirección de correo electrónico',
            'Cuentenos sus areas de experiencia. Necesitamos una descripción detallada de su experiencia laboral. Esta información es clave para realizar una búsqueda efectiva y presentarle a las vacantes más adecuadas',
            'Ciudad', '¿cuenta usted con disponibilidad de trabajar turnos rotativos?', '¿Cuenta con transporte propio ?',
            '¿Cual es su grado academico ?', 'Dejenos Su Cv(Enlace a Google Drive)',
            'Foto revés y derecho de su tarjeta de identidad:(enlace Google Drive )', 'Estado', 'Observaciones'
        ],
        'clientes': ['empresa', 'contacto_nombre', 'telefono', 'email', 'sector', 'observaciones'],
        'vacantes': ['id_cliente (ID numérico del cliente)', 'cargo_solicitado', 'ciudad', 'requisitos', 'salario', 'estado'],
        'postulaciones': ['identidad_candidato (Sin guiones)', 'id_vacante (ID numérico de la vacante)', 'comentarios', 'estado'],
        'entrevistas': ['id_postulacion', 'fecha_hora (YYYY-MM-DD HH:MM:SS)', 'entrevistador', 'resultado', 'observaciones'],
        'contratados': ['id_afiliado', 'id_vacante', 'fecha_contratacion (YYYY-MM-DD)', 'salario_final']
    }
    headers = TEMPLATE_HEADERS.get(data_type)
    if not headers:
        return jsonify({"success": False, "error": "Tipo de plantilla no válido."}), 400
    df = pd.DataFrame(columns=headers)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=data_type)
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'plantilla_{data_type}.xlsx'
    )


@app.route('/api/upload-excel', methods=['POST'])
@token_required
def upload_excel():
    if 'file' not in request.files: return jsonify({"success": False, "error": "No se encontró ningún archivo."}), 400
    data_type = request.form.get('type', 'afiliados')
    file = request.files['file']
    if file.filename == '': return jsonify({"success": False, "error": "No se seleccionó ningún archivo."}), 400
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')): return jsonify({"success": False, "error": "Formato de archivo no válido."}), 400

    try:
        df = pd.read_excel(file, engine='openpyxl')
        # ✨ CORRECCIÓN PRINCIPAL AQUÍ ✨
        # Reemplazamos los valores vacíos (NaN) de pandas por None de Python.
        # La condición ahora se aplica a la tabla de datos (df) misma.
        df = df.astype(object).where(df.notna(), None)

        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "error": "Error de conexión a la BD."}), 500
        cursor = conn.cursor()
        processed_count = 0

        if data_type == 'afiliados':
            # La lógica para afiliados se mantiene igual, si la tenías.
            # Por ahora la dejamos pasar para enfocarnos en clientes.
            pass
        
        # ✨ LÓGICA PARA CLIENTES AÑADIDA AQUÍ ✨
        elif data_type == 'clientes':
            # Columnas esperadas en la plantilla de clientes
            # ['empresa', 'contacto_nombre', 'telefono', 'email', 'sector', 'observaciones']
            for _, row in df.iterrows():
                # Validamos que la empresa (campo obligatorio) no esté vacía
                if not row.get('empresa'):
                    continue # Si no hay nombre de empresa, saltamos esta fila

                sql = """
                    INSERT INTO Clientes (empresa, contacto_nombre, telefono, email, sector, observaciones, tenant_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        contacto_nombre=VALUES(contacto_nombre), telefono=VALUES(telefono),
                        email=VALUES(email), sector=VALUES(sector), observaciones=VALUES(observaciones);
                """
                params = (
                    row.get('empresa'),
                    row.get('contacto_nombre'),
                    row.get('telefono'),
                    row.get('email'),
                    row.get('sector'),
                    row.get('observaciones'),
                    tenant_id
                )
                cursor.execute(sql, params)
                processed_count += 1
        
        elif data_type == 'postulaciones':
            # La lógica para postulaciones se mantiene igual, si la tenías.
            pass

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": f"{processed_count} registros de '{data_type}' procesados correctamente."})

    except Exception as e:
        # Devolvemos el error específico para facilitar la depuración
        return jsonify({"success": False, "error": f"Error al procesar el archivo: {str(e)}"}), 500

# ===============================================================
# SECCIÓN 3: GESTIÓN DE ETIQUETAS Y COMUNICACIONES
# ===============================================================
@app.route('/api/tags', methods=['GET', 'POST'])
@token_required
def handle_tags():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        
        if request.method == 'GET':
            cursor.execute("SELECT * FROM Tags WHERE tenant_id = %s ORDER BY nombre_tag", (tenant_id,))
            return jsonify(cursor.fetchall())
        
        elif request.method == 'POST':
            data = request.get_json()
            nombre_tag = data.get('nombre_tag')
            if not nombre_tag:
                return jsonify({"success": False, "error": "El nombre del tag es requerido."}), 400
            
            cursor.execute("INSERT INTO Tags (nombre_tag, tenant_id) VALUES (%s, %s)", (nombre_tag, tenant_id))
            conn.commit()
            return jsonify({"success": True, "message": "Tag creado exitosamente.", "id_tag": cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        if err.errno == 1062:  # Duplicate entry
            return jsonify({"success": False, "error": "Ya existe un tag con ese nombre."}), 409
        return jsonify({"success": False, "error": f"Error de base de datos: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/candidate/<int:id_afiliado>/tags', methods=['GET', 'POST', 'DELETE'])
@token_required
def handle_candidate_tags(id_afiliado):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        
        # Verificar que el candidato pertenece al tenant
        cursor.execute("SELECT id_afiliado FROM Afiliados WHERE id_afiliado = %s AND tenant_id = %s", (id_afiliado, tenant_id))
        if not cursor.fetchone():
            return jsonify({"error": "Candidato no encontrado"}), 404
        
        if request.method == 'GET':
            sql = """
                SELECT T.id_tag, T.nombre_tag 
                FROM Afiliado_Tags AT 
                JOIN Tags T ON AT.id_tag = T.id_tag 
                WHERE AT.id_afiliado = %s AND T.id_cliente = %s
            """
            cursor.execute(sql, (id_afiliado, tenant_id))
            return jsonify(cursor.fetchall())
        elif request.method == 'POST':
            data = request.get_json()
            id_tag = data.get('id_tag')
            if not id_tag: return jsonify({"error": "Se requiere id_tag"}), 400
            
            # Verificar que el tag pertenece al tenant
            cursor.execute("SELECT id_tag FROM Tags WHERE id_tag = %s AND tenant_id = %s", (id_tag, tenant_id))
            if not cursor.fetchone():
                return jsonify({"error": "Tag no encontrado"}), 404
            
            cursor.execute("INSERT INTO Afiliado_Tags (id_afiliado, id_tag, tenant_id) VALUES (%s, %s, %s)", (id_afiliado, id_tag, tenant_id))
            conn.commit()
            return jsonify({"success": True, "message": "Etiqueta asignada."}), 201
        elif request.method == 'DELETE':
            data = request.get_json()
            id_tag = data.get('id_tag')
            if not id_tag: return jsonify({"error": "Se requiere id_tag"}), 400
            cursor.execute("DELETE FROM Afiliado_Tags WHERE id_afiliado = %s AND id_tag = %s AND tenant_id = %s", (id_afiliado, id_tag, tenant_id))
            conn.commit()
            return jsonify({"success": True, "message": "Etiqueta removida."})
    except mysql.connector.Error as err:
        if err.errno == 1062: return jsonify({"success": False, "error": "El candidato ya tiene esta etiqueta."}), 409
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/templates', methods=['GET', 'POST'])
@token_required
def handle_email_templates():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        
        if request.method == 'GET':
            cursor.execute("SELECT id_template, nombre_plantilla, asunto, fecha_creacion FROM Email_Templates WHERE tenant_id = %s ORDER BY nombre_plantilla", (tenant_id,))
            return jsonify(cursor.fetchall())
        elif request.method == 'POST':
            data = request.get_json()
            sql = "INSERT INTO Email_Templates (nombre_plantilla, asunto, cuerpo_html, tenant_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (data['nombre_plantilla'], data['asunto'], data['cuerpo_html'], tenant_id))
            conn.commit()
            return jsonify({"success": True, "message": "Plantilla creada."}), 201
    finally:
        cursor.close()
        conn.close()

@app.route('/api/templates/<int:id_template>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def handle_single_template(id_template):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        
        if request.method == 'GET':
            cursor.execute("SELECT * FROM Email_Templates WHERE id_template = %s AND tenant_id = %s", (id_template, tenant_id))
            template = cursor.fetchone()
            if not template: return jsonify({"error": "Plantilla no encontrada"}), 404
            return jsonify(template)
        elif request.method == 'PUT':
            data = request.get_json()
            sql = "UPDATE Email_Templates SET nombre_plantilla=%s, asunto=%s, cuerpo_html=%s WHERE id_template=%s AND id_cliente=%s"
            cursor.execute(sql, (data['nombre_plantilla'], data['asunto'], data['cuerpo_html'], id_template, tenant_id))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"error": "Plantilla no encontrada"}), 404
            return jsonify({"success": True, "message": "Plantilla actualizada."})
        elif request.method == 'DELETE':
            cursor.execute("DELETE FROM Email_Templates WHERE id_template = %s AND tenant_id = %s", (id_template, tenant_id))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"error": "Plantilla no encontrada"}), 404
            return jsonify({"success": True, "message": "Plantilla eliminada."})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/communications/send-email', methods=['POST'])
@token_required
def send_email_from_template():
    data = request.get_json()
    id_afiliado = data.get('id_afiliado')
    id_template = data.get('id_template')

    if not id_afiliado or not id_template:
        return jsonify({"error": "Faltan id_afiliado o id_template"}), 400

    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)

    try:
        tenant_id = get_current_tenant_id()
        
        cursor.execute("SELECT nombre_completo, email FROM Afiliados WHERE id_afiliado = %s AND tenant_id = %s", (id_afiliado, tenant_id))
        candidato = cursor.fetchone()
        if not candidato: return jsonify({"error": "Candidato no encontrado"}), 404

        cursor.execute("SELECT asunto, cuerpo_html FROM Email_Templates WHERE id_template = %s AND tenant_id = %s", (id_template, tenant_id))
        template = cursor.fetchone()
        if not template: return jsonify({"error": "Plantilla no encontrada"}), 404

        nombre_candidato = candidato['nombre_completo'].split(' ')[0]
        asunto_personalizado = template['asunto'].replace('[name]', nombre_candidato)
        cuerpo_personalizado = template['cuerpo_html'].replace('[name]', nombre_candidato)

        sender_email = os.getenv('GMAIL_USER')
        password = os.getenv('GMAIL_APP_PASSWORD')
        receiver_email = candidato['email']

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = asunto_personalizado
        msg.attach(MIMEText(cuerpo_personalizado, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()

        return jsonify({"success": True, "message": f"Correo enviado a {candidato['nombre_completo']}."})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# AÑADE ESTE NUEVO BLOQUE DE CÓDIGO en app.py

@app.route('/api/whatsapp-templates-legacy', methods=['GET', 'POST'])
@token_required
def handle_whatsapp_templates():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        
        if request.method == 'GET':
            cursor.execute("SELECT id_template, nombre_plantilla FROM Whatsapp_Templates WHERE tenant_id = %s ORDER BY nombre_plantilla", (tenant_id,))
            return jsonify(cursor.fetchall())
        elif request.method == 'POST':
            data = request.get_json()
            sql = "INSERT INTO Whatsapp_Templates (nombre_plantilla, cuerpo_mensaje, tenant_id) VALUES (%s, %s, %s)"
            cursor.execute(sql, (data['nombre_plantilla'], data['cuerpo_mensaje'], tenant_id))
            conn.commit()
            return jsonify({"success": True, "message": "Plantilla de WhatsApp creada."}), 201
    finally:
        cursor.close()
        conn.close()



# ===============================================================
# SECCIÓN 4: PIPELINE Y FLUJO DE TRABAJO
# ===============================================================
@app.route('/api/vacancies/<int:id_vacante>/pipeline', methods=['GET'])
@token_required
def get_vacancy_pipeline(id_vacante):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        user_role = getattr(g, 'current_user', {}).get('rol', '')
        
        # Para administradores, permitir ver cualquier vacante
        # Para otros usuarios, verificar que la vacante pertenece al tenant
        if user_role == 'Administrador':
            cursor.execute("SELECT id_vacante FROM Vacantes WHERE id_vacante = %s", (id_vacante,))
        else:
            cursor.execute("SELECT id_vacante FROM Vacantes WHERE id_vacante = %s AND tenant_id = %s", (id_vacante, tenant_id))
        
        if not cursor.fetchone():
            return jsonify({"error": "Vacante no encontrada"}), 404
        
        # Para administradores, mostrar todas las postulaciones de la vacante
        # Para otros usuarios, filtrar por tenant
        if user_role == 'Administrador':
            sql = """
                SELECT p.id_postulacion, p.estado, a.id_afiliado, a.nombre_completo, a.cv_url 
                FROM Postulaciones p 
                JOIN Afiliados a ON p.id_afiliado = a.id_afiliado 
                WHERE p.id_vacante = %s
            """
            cursor.execute(sql, (id_vacante,))
        else:
            sql = """
            SELECT p.id_postulacion, p.estado, a.id_afiliado, a.nombre_completo, a.cv_url 
            FROM Postulaciones p 
            JOIN Afiliados a ON p.id_afiliado = a.id_afiliado 
            WHERE p.id_vacante = %s AND p.id_cliente = %s
        """
        cursor.execute(sql, (id_vacante, tenant_id))
        postulaciones = cursor.fetchall()
        pipeline = {'Recibida': [], 'En Revisión': [], 'Pre-seleccionado': [], 'En Entrevista': [], 'Oferta': [], 'Contratado': [], 'Rechazado': []}
        for post in postulaciones:
            estado = post.get('estado', 'Recibida')
            if estado in pipeline:
                pipeline[estado].append(post)
        return jsonify(pipeline)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/applications/<int:id_postulacion>/status', methods=['PUT'])
@token_required
def update_application_status(id_postulacion):
    data = request.get_json()
    # Aceptar tanto 'estado' como 'status' para compatibilidad
    nuevo_estado = data.get('estado') or data.get('status')
    if not nuevo_estado: return jsonify({"error": "El nuevo estado es requerido"}), 400
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor()
    try:
        tenant_id = get_current_tenant_id()
        
        # Verificar que la postulación pertenece al tenant a través de Vacantes
        cursor.execute("""
            SELECT p.id_postulacion, p.id_afiliado, p.id_vacante, v.id_cliente
            FROM Postulaciones p
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE p.id_postulacion = %s AND v.tenant_id = %s
        """, (id_postulacion, tenant_id))
        postulacion_data = cursor.fetchone()
        if not postulacion_data:
            return jsonify({"error": "Postulación no encontrada"}), 404
        
        # Actualizar el estado de la postulación
        cursor.execute("UPDATE Postulaciones SET estado = %s WHERE id_postulacion = %s", (nuevo_estado, id_postulacion))
        
        # Si el nuevo estado es "Contratado", registrar en la tabla Contratados
        if nuevo_estado.lower() in ['contratado', 'hired', 'aceptado']:
            id_afiliado, id_vacante, id_cliente = postulacion_data[1], postulacion_data[2], postulacion_data[3]
            
            # Verificar si ya existe en Contratados
            cursor.execute("""
                SELECT id_contratado FROM Contratados 
                WHERE id_afiliado = %s AND id_vacante = %s
            """, (id_afiliado, id_vacante))
            
            if not cursor.fetchone():
                # Insertar en tabla Contratados
                cursor.execute("""
                    INSERT INTO Contratados (id_afiliado, id_vacante, id_cliente, fecha_contratacion, estado, tenant_id)
                    VALUES (%s, %s, %s, NOW(), 'Activo', %s)
                """, (id_afiliado, id_vacante, id_cliente, tenant_id))
                app.logger.info(f"Candidato {id_afiliado} contratado para vacante {id_vacante}")
        
        conn.commit()
        return jsonify({"success": True, "message": f"Postulación actualizada a {nuevo_estado}."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ===============================================================
# SECCIÓN 5: REPORTES Y KPIS
# ===============================================================
@app.route('/api/reports/kpi', methods=['GET'])
@token_required
def get_kpi_reports():
    """
    Devuelve KPIs completos para el dashboard de analytics.
    Incluye métricas de tiempo, conversión, rendimiento, etc.
    """
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        
        # 1. Métricas de tiempo
        cursor.execute("""
            SELECT AVG(DATEDIFF(fecha_cierre, fecha_apertura)) as avg_time_to_fill 
            FROM Vacantes 
            WHERE estado = 'Cerrada' AND fecha_cierre IS NOT NULL AND fecha_apertura IS NOT NULL
        """)
        time_to_fill = cursor.fetchone()['avg_time_to_fill']
        
        cursor.execute("""
            SELECT AVG(DATEDIFF(c.fecha_contratacion, p.fecha_aplicacion)) as avg_time_to_hire 
            FROM Contratados c 
            JOIN Postulaciones p ON c.id_afiliado = p.id_afiliado AND c.id_vacante = p.id_vacante
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
        """)
        time_to_hire = cursor.fetchone()['avg_time_to_hire']
        
        # 2. Embudo de conversión
        cursor.execute("""
            SELECT p.estado, COUNT(*) as total 
            FROM Postulaciones p
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            GROUP BY p.estado
        """)
        funnel_data = cursor.fetchall()
        funnel = {row['estado']: row['total'] for row in funnel_data}
        total_aplicaciones = sum(funnel.values())
        conversion_rates = {}
        if total_aplicaciones > 0:
            for estado, total in funnel.items():
                rate = (total / total_aplicaciones) * 100
                conversion_rates[estado] = round(rate, 2)
        
        # 3. Métricas de candidatos
        cursor.execute("""
            SELECT COUNT(*) as total_candidates FROM Afiliados
        """)
        total_candidates = cursor.fetchone()['total_candidates']
        
        cursor.execute("""
            SELECT COUNT(*) as new_this_month FROM Afiliados 
            WHERE MONTH(fecha_registro) = MONTH(CURDATE()) 
            AND YEAR(fecha_registro) = YEAR(CURDATE())
        """)
        new_candidates_month = cursor.fetchone()['new_this_month']
        
        # 4. Métricas de vacantes
        cursor.execute("""
            SELECT COUNT(*) as active_vacancies FROM Vacantes 
            WHERE estado = 'Activa'
        """)
        active_vacancies = cursor.fetchone()['active_vacancies']
        
        cursor.execute("""
            SELECT COUNT(*) as filled_vacancies FROM Vacantes 
            WHERE estado = 'Cerrada'
        """)
        filled_vacancies = cursor.fetchone()['filled_vacancies']
        
        # 5. Métricas de entrevistas
        cursor.execute("""
            SELECT COUNT(*) as total_interviews FROM Entrevistas e
            JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
        """)
        total_interviews = cursor.fetchone()['total_interviews']
        
        cursor.execute("""
            SELECT COUNT(*) as interviews_today FROM Entrevistas e
            JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE DATE(e.fecha_hora) = CURDATE()
        """)
        interviews_today = cursor.fetchone()['interviews_today']
        
        # 6. Tasa de éxito por canal (si tienes datos de canal)
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN fuente_reclutamiento IS NOT NULL AND fuente_reclutamiento != '' 
                    THEN fuente_reclutamiento 
                    ELSE 'No especificado' 
                END as canal,
                COUNT(*) as total,
                COUNT(CASE WHEN EXISTS(
                    SELECT 1 FROM Contratados c 
                    WHERE c.id_afiliado = a.id_afiliado
                ) THEN 1 END) as contratados
            FROM Afiliados a
            GROUP BY canal
        """)
        channel_data = cursor.fetchall()
        channel_performance = []
        for row in channel_data:
            success_rate = (row['contratados'] / row['total'] * 100) if row['total'] > 0 else 0
            channel_performance.append({
                'canal': row['canal'],
                'total': row['total'],
                'contratados': row['contratados'],
                'tasa_exito': round(success_rate, 2)
            })
        
        # 7. Métricas de satisfacción (simuladas basadas en resultados de entrevistas)
        cursor.execute("""
            SELECT resultado, COUNT(*) as count FROM Entrevistas e
            JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE resultado != 'Programada'
            GROUP BY resultado
        """)
        interview_results = cursor.fetchall()
        satisfaction_metrics = {
            'excellent': 0,
            'good': 0,
            'average': 0,
            'poor': 0
        }
        for result in interview_results:
            if result['resultado'] in ['Contratado', 'Excelente']:
                satisfaction_metrics['excellent'] += result['count']
            elif result['resultado'] in ['Aprobado', 'Bueno']:
                satisfaction_metrics['good'] += result['count']
            elif result['resultado'] in ['Regular', 'Pendiente']:
                satisfaction_metrics['average'] += result['count']
            else:
                satisfaction_metrics['poor'] += result['count']
        
        return jsonify({
            "success": True,
            "data": {
                "time_metrics": {
                "avgTimeToFillDays": round(time_to_fill, 1) if time_to_fill else 0,
                    "avgTimeToHireDays": round(time_to_hire, 1) if time_to_hire else 0
                },
                "conversion_funnel": {
                    "raw": funnel,
                    "percentages": conversion_rates,
                    "total_applications": total_aplicaciones
                },
                "candidate_metrics": {
                    "total_candidates": total_candidates,
                    "new_this_month": new_candidates_month,
                    "growth_rate": round((new_candidates_month / total_candidates * 100), 2) if total_candidates > 0 else 0
                },
                "vacancy_metrics": {
                    "active_vacancies": active_vacancies,
                    "filled_vacancies": filled_vacancies,
                    "fill_rate": round((filled_vacancies / (active_vacancies + filled_vacancies) * 100), 2) if (active_vacancies + filled_vacancies) > 0 else 0
                },
                "interview_metrics": {
                    "total_interviews": total_interviews,
                    "interviews_today": interviews_today,
                    "interview_rate": round((total_interviews / total_aplicaciones * 100), 2) if total_aplicaciones > 0 else 0
                },
                "channel_performance": channel_performance,
                "satisfaction_metrics": satisfaction_metrics
            }
        })
    except Exception as e:
        app.logger.error(f"Error en get_kpi_reports: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


def _internal_search_candidates(term=None, tags=None, experience=None, city=None, recency_days=None, 
                           registered_today=False, status=None, availability=None, min_score=None,
                           limit=None, offset=None):
    """
    Lógica de búsqueda interna que puede ser llamada desde la API o el Asistente.
    
    Args:
        term (str, optional): Término de búsqueda general.
        tags (str, optional): Lista de IDs de etiquetas separadas por comas.
        experience (str, optional): Filtro por experiencia.
        city (str, optional): Filtro por ciudad.
        recency_days (int, optional): Filtrar por días desde el registro.
        registered_today (bool, optional): Solo registrados hoy.
        status (str, optional): Filtro por estado del candidato.
        availability (str, optional): Filtro por disponibilidad.
        min_score (int, optional): Puntuación mínima.
        limit (int, optional): Límite de resultados.
        offset (int, optional): Desplazamiento para paginación.
        
    Returns:
        list: Lista de candidatos con formato estandarizado para la interfaz.
    """
    conn = get_db_connection()
    if not conn: 
        app.logger.error("No se pudo establecer conexión con la base de datos")
        return []
        
    cursor = conn.cursor(dictionary=True)
    try:
        # Consulta base con los campos necesarios para la interfaz
        base_query = """
            SELECT 
                a.id_afiliado as id,
                a.nombre_completo as name,
                a.email as email,
                a.telefono as phone,
                a.ciudad as location,
                a.experiencia as experience,
                a.estado as status,
                a.puntuacion as score,
                a.fecha_registro as createdAt,
                NULL as lastContact,
                NULL as availability,
                NULL as desiredSalary,
                NULL as education,
                a.habilidades as skills,
                
                -- Campos adicionales para la vista detallada
                NULL as birthDate,
                NULL as address,
                NULL as gender,
                NULL as maritalStatus,
                
                -- Campos simplificados para evitar errores
                NULL as previousCompanies,
                NULL as tags_json,
                0 as documentsCount,
                NULL as lastInteractionType,
                NULL as lastInteractionDate
                
            FROM Afiliados a
            WHERE 1=1
        """
        
        # Lista de condiciones de filtrado
        conditions = []
        params = []

        # Filtro por término de búsqueda
        if term:
            if term.isdigit():
                conditions.append("""
                    (a.nombre_completo LIKE %s 
                    OR a.experiencia LIKE %s 
                    OR a.ciudad LIKE %s 
                    OR a.id_afiliado = %s 
                    OR a.email LIKE %s)
                """)
                params.extend([f"%{term}%", f"%{term}%", f"%{term}%", term, f"%{term}%"])
            else:
                search_terms = term.split()
                term_conditions = []
                for t in search_terms:
                    term_conditions.append("""
                        (a.nombre_completo LIKE %s 
                        OR a.experiencia LIKE %s 
                        OR a.ciudad LIKE %s 
                        OR a.cargo_solicitado LIKE %s
                        OR a.habilidades LIKE %s)
                    """)
                    params.extend([f"%{t}%", f"%{t}%", f"%{t}%", f"%{t}%", f"%{t}%"])
                conditions.append(f"({' OR '.join(term_conditions)})" if len(term_conditions) > 1 else term_conditions[0])
        
        # Filtros adicionales
        if experience:
            conditions.append("a.experiencia LIKE %s")
            params.append(f"%{experience}%")
            
        if city:
            conditions.append("a.ciudad LIKE %s")
            params.append(f"%{city}%")
            
        if recency_days and str(recency_days).isdigit():
            conditions.append("a.fecha_registro >= CURDATE() - INTERVAL %s DAY")
            params.append(int(recency_days))
            
        if registered_today:
            conditions.append("DATE(a.fecha_registro) = CURDATE()")
            
        if status:
            conditions.append("a.estado = %s")
            params.append(status)
            
        if availability:
            conditions.append("a.disponibilidad = %s")
            params.append(availability)
            
        if min_score and min_score.isdigit():
            conditions.append("a.puntuacion >= %s")
            params.append(int(min_score))

        # Aplicar condiciones de filtrado
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # Ordenar por fecha de registro por defecto
        base_query += " ORDER BY a.fecha_registro DESC"
        
        # Aplicar paginación si se especifica
        if limit is not None and offset is not None:
            base_query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
        
        # Ejecutar la consulta
        app.logger.info(f"Ejecutando consulta: {base_query}")
        app.logger.info(f"Parámetros: {params}")
        
        cursor.execute(base_query, tuple(params))
        results = cursor.fetchall()
        
        # Procesar resultados
        formatted_results = []
        for row in results:
            # Convertir fechas a formato ISO
            for date_field in ['createdAt', 'lastContact', 'birthDate', 'lastInteractionDate']:
                if row.get(date_field) and isinstance(row[date_field], datetime):
                    row[date_field] = row[date_field].isoformat()
            
            # Convertir JSON de tags a objeto Python
            if row.get('tags_json'):
                try:
                    row['tags'] = json.loads(row.pop('tags_json'))
                except json.JSONDecodeError:
                    row['tags'] = []
            else:
                row['tags'] = []
            
            # Procesar habilidades para enviar solo las tecnologías como array
            if row.get('skills'):
                try:
                    skills_data = json.loads(row['skills'])
                    if isinstance(skills_data, dict) and 'tecnologias' in skills_data:
                        # Extraer solo las tecnologías del objeto JSON
                        row['skills'] = skills_data['tecnologias']
                    else:
                        row['skills'] = []
                except (json.JSONDecodeError, TypeError):
                    # Si no es un JSON válido, convertirlo a una lista
                    row['skills'] = [skill.strip() for skill in str(row['skills']).split(',') if skill.strip()]
            else:
                row['skills'] = []
            
            # Asegurar que los campos opcionales tengan valores por defecto
            row['documentsCount'] = row.get('documentsCount', 0)
            row['status'] = row.get('status', 'nuevo')
            row['score'] = float(row['score']) if row.get('score') is not None else 0.0
            
            # Agregar URL de avatar (puedes personalizar esto según tu lógica)
            row['avatar'] = f"https://ui-avatars.com/api/?name={row['name'].replace(' ', '+')}&background=random"
            
            formatted_results.append(row)

        return formatted_results
        
    except Exception as e:
        app.logger.error(f"Error en _internal_search_candidates: {str(e)}")
        app.logger.error(traceback.format_exc())
        return []
        
    finally: 
        cursor.close()
        conn.close()


def search_candidates_tool(term=None, tags=None, experience=None, city=None, recency_days=None):
    """Herramienta para el Asistente: Busca candidatos y devuelve los resultados en formato JSON."""
    app.logger.info(f"Búsqueda de candidatos con: term={term}, tags={tags}, experience={experience}, city={city}")
    results = _internal_search_candidates(term, tags, experience, city, recency_days)
    return json.dumps(results)




# ===============================================================
# SECCIÓN DE REPORTES AVANZADOS
# ===============================================================


@app.route('/api/reports', methods=['GET'])
@token_required
def get_reports():
    report_name = request.args.get('name', 'summary')

    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Si no se especifica reporte o es 'summary', devolver resumen general
        if report_name == 'summary' or report_name == 'all':
            # Reporte de resumen general
            cursor.execute("""
                SELECT 
                    'Candidatos' as tipo,
                    COUNT(*) as total,
                    'Registrados en el sistema' as descripcion
                FROM Afiliados
                UNION ALL
                SELECT 
                    'Vacantes Activas' as tipo,
                    COUNT(*) as total,
                    'Vacantes abiertas actualmente' as descripcion
                FROM Vacantes WHERE estado = 'Activa'
                UNION ALL
                SELECT 
                    'Entrevistas Hoy' as tipo,
                    COUNT(*) as total,
                    'Entrevistas programadas para hoy' as descripcion
                FROM Entrevistas WHERE DATE(fecha_hora) = CURDATE()
            """)
            results = cursor.fetchall()
            
            return jsonify({
                "success": True,
                "data": results,
                "report_name": "summary"
            })
        
        # Reportes específicos (simplificados)
        if report_name == 'vacantes_activas':
            cursor.execute("SELECT id_vacante, cargo_solicitado, fecha_apertura FROM Vacantes WHERE estado = 'Activa' LIMIT 10")
            results = cursor.fetchall()
        elif report_name == 'postulaciones_recientes':
            cursor.execute("SELECT a.nombre_completo, v.cargo_solicitado, p.fecha_aplicacion FROM Postulaciones p JOIN Afiliados a ON p.id_afiliado = a.id_afiliado JOIN Vacantes v ON p.id_vacante = v.id_vacante ORDER BY p.fecha_aplicacion DESC LIMIT 10")
            results = cursor.fetchall()
        elif report_name == 'entrevistas_agendadas':
            cursor.execute("SELECT e.fecha_hora, a.nombre_completo, v.cargo_solicitado FROM Entrevistas e JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion JOIN Afiliados a ON p.id_afiliado = a.id_afiliado JOIN Vacantes v ON p.id_vacante = v.id_vacante WHERE DATE(e.fecha_hora) >= CURDATE() LIMIT 10")
            results = cursor.fetchall()
        else:
            # Para cualquier otro reporte, devolver mensaje de no encontrado
            return jsonify({
                "success": False,
                "error": f"El reporte '{report_name}' no está disponible"
            }), 404
        
        return jsonify({
            "success": True,
            "data": results,
            "report_name": report_name
        })

    except Exception as e:
        return jsonify({"error": f"Error al generar el reporte: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()





# ===============================================================
# SECCIÓN 6: ENDPOINTS PRINCIPALES (CRUDs Y BÚSQUEDAS)
# ===============================================================
@app.route('/api/dashboard', methods=['GET'])
@token_required
def get_dashboard_data():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de conexión"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Métricas básicas
        cursor.execute("SELECT COUNT(*) as total FROM Entrevistas WHERE fecha_hora >= CURDATE()")
        entrevistas_pendientes = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM Entrevistas WHERE fecha_hora < CURDATE() AND resultado = 'Programada'")
        entrevistas_sin_resultado = cursor.fetchone()['total']
        
        # Estadísticas de vacantes
        cursor.execute("SELECT V.cargo_solicitado, C.empresa, COUNT(P.id_postulacion) as postulantes FROM Postulaciones P JOIN Vacantes V ON P.id_vacante = V.id_vacante JOIN Clientes C ON V.id_cliente = C.id_cliente GROUP BY V.id_vacante, V.cargo_solicitado, C.empresa ORDER BY postulantes DESC")
        estadisticas_vacantes = cursor.fetchall()
        
        # Candidatos
        cursor.execute("SELECT COUNT(*) as total FROM Afiliados WHERE DATE(fecha_registro) = CURDATE()")
        afiliados_hoy = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM Afiliados WHERE MONTH(fecha_registro) = MONTH(CURDATE()) AND YEAR(fecha_registro) = YEAR(CURDATE())")
        afiliados_mes = cursor.fetchone()['total']
        
        # Top ciudades
        cursor.execute("SELECT ciudad, COUNT(*) as total FROM Afiliados WHERE ciudad IS NOT NULL AND ciudad != '' GROUP BY ciudad ORDER BY total DESC LIMIT 5")
        top_ciudades = cursor.fetchall()
        
        return jsonify({
            "success": True, 
            "entrevistasPendientes": entrevistas_pendientes,
            "entrevistasSinResultado": entrevistas_sin_resultado,
            "vacantesMasPostuladas": estadisticas_vacantes[:5],
            "vacantesMenosPostuladas": sorted(estadisticas_vacantes, key=lambda x: x['postulantes'])[:5],
            "afiliadosHoy": afiliados_hoy, 
            "afiliadosEsteMes": afiliados_mes,
            "topCiudades": top_ciudades
        })
    except Exception as e: return jsonify({"success": False, "error": str(e)}), 500
    finally: cursor.close(); conn.close()

@app.route('/api/dashboard/metrics', methods=['GET'])
@token_required
def get_dashboard_metrics():
    """
    Endpoint mejorado para métricas del dashboard con datos más completos
    """
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de conexión"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Candidatos activos totales
        cursor.execute("SELECT COUNT(*) as total FROM Afiliados")
        total_candidatos = cursor.fetchone()['total']
        
        # 2. Candidatos activos hoy
        cursor.execute("SELECT COUNT(*) as total FROM Afiliados WHERE DATE(fecha_registro) = CURDATE()")
        candidatos_hoy = cursor.fetchone()['total']
        
        # 3. Vacantes por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as total 
            FROM Vacantes 
            GROUP BY estado
        """)
        vacantes_por_estado = cursor.fetchall()
        
        # 4. Tasa de conversión (postulaciones → contrataciones)
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT p.id_postulacion) as total_postulaciones,
                COUNT(DISTINCT c.id_contratado) as total_contrataciones
            FROM Postulaciones p
            LEFT JOIN Contratados c ON p.id_afiliado = c.id_afiliado AND p.id_vacante = c.id_vacante
        """)
        conversion_data = cursor.fetchone()
        tasa_conversion = (conversion_data['total_contrataciones'] / conversion_data['total_postulaciones'] * 100) if conversion_data['total_postulaciones'] > 0 else 0
        
        # 5. Tiempo promedio de contratación
        cursor.execute("""
            SELECT AVG(DATEDIFF(c.fecha_contratacion, p.fecha_aplicacion)) as tiempo_promedio
            FROM Contratados c
            JOIN Postulaciones p ON c.id_afiliado = p.id_afiliado AND c.id_vacante = p.id_vacante
            WHERE c.fecha_contratacion IS NOT NULL AND p.fecha_aplicacion IS NOT NULL
        """)
        tiempo_promedio = cursor.fetchone()['tiempo_promedio'] or 0
        
        # 6. Candidatos por mes (últimos 6 meses)
        cursor.execute("""
            SELECT 
                DATE_FORMAT(fecha_registro, '%Y-%m') as mes,
                COUNT(*) as total
            FROM Afiliados 
            WHERE fecha_registro >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(fecha_registro, '%Y-%m')
            ORDER BY mes
        """)
        candidatos_por_mes = cursor.fetchall()
        
        # 7. Ingresos generados (si aplica)
        cursor.execute("""
            SELECT SUM(COALESCE(tarifa_servicio, 0)) as ingresos_totales
            FROM Contratados
            WHERE fecha_contratacion >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        """)
        ingresos_totales = cursor.fetchone()['ingresos_totales'] or 0
        
        # 8. Top 5 clientes por actividad
        cursor.execute("""
            SELECT 
                c.empresa,
                COUNT(DISTINCT v.id_vacante) as total_vacantes,
                COUNT(DISTINCT p.id_postulacion) as total_postulaciones,
                COUNT(DISTINCT co.id_contratado) as total_contrataciones
            FROM Clientes c
            LEFT JOIN Vacantes v ON c.id_cliente = v.id_cliente AND v.tenant_id = %s
            LEFT JOIN Postulaciones p ON v.id_vacante = p.id_vacante AND p.tenant_id = %s
            LEFT JOIN Contratados co ON v.id_vacante = co.id_vacante AND co.tenant_id = %s
            WHERE c.tenant_id = %s
            GROUP BY c.id_cliente, c.empresa
            ORDER BY total_postulaciones DESC
            LIMIT 5
        """, (tenant_id, tenant_id, tenant_id, tenant_id))
        top_clientes = cursor.fetchall()
        
        # 9. Efectividad por usuario (si tenemos tabla de usuarios)
        cursor.execute("""
            SELECT 
                'Usuario Demo' as usuario,
                COUNT(DISTINCT p.id_postulacion) as total_postulaciones,
                COUNT(DISTINCT co.id_contratado) as total_contrataciones
            FROM Postulaciones p
            LEFT JOIN Contratados co ON p.id_afiliado = co.id_afiliado AND p.id_vacante = co.id_vacante
        """)
        efectividad_usuario = cursor.fetchone()
        
        # 10. Tasa de éxito por tipo de vacante
        cursor.execute("""
            SELECT 
                v.cargo_solicitado,
                COUNT(DISTINCT p.id_postulacion) as total_postulaciones,
                COUNT(DISTINCT co.id_contratado) as total_contrataciones,
                CASE 
                    WHEN COUNT(DISTINCT p.id_postulacion) > 0 THEN
                        (COUNT(DISTINCT co.id_contratado) * 100.0 / COUNT(DISTINCT p.id_postulacion))
                    ELSE 0
                END as tasa_exito
            FROM Vacantes v
            LEFT JOIN Postulaciones p ON v.id_vacante = p.id_vacante
            LEFT JOIN Contratados co ON v.id_vacante = co.id_vacante
            GROUP BY v.id_vacante, v.cargo_solicitado
            HAVING total_postulaciones > 0
            ORDER BY tasa_exito DESC
            LIMIT 5
        """)
        tasa_exito_vacantes = cursor.fetchall()
        
        return jsonify({
            "success": True,
            "data": {
                "total_candidatos": total_candidatos,
                "candidatos_hoy": candidatos_hoy,
                "vacantes_por_estado": vacantes_por_estado,
                "tasa_conversion": round(tasa_conversion, 2),
                "tiempo_promedio_contratacion": int(tiempo_promedio),
                "candidatos_por_mes": candidatos_por_mes,
                "ingresos_totales": float(ingresos_totales),
                "top_clientes": top_clientes,
                "efectividad_usuario": efectividad_usuario,
                "tasa_exito_vacantes": tasa_exito_vacantes
            }
        })
        
    except Exception as e: 
        app.logger.error(f"Error en dashboard metrics: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally: 
        cursor.close(); conn.close()


@app.route('/api/candidates', methods=['GET', 'POST'])
@token_required
def handle_candidates():
    """Maneja candidatos: GET para listar, POST para crear."""
    if request.method == 'GET':
        return get_candidates()
    elif request.method == 'POST':
        return create_candidate()

def get_candidates():
    """Obtiene la lista de candidatos."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        tenant_id = get_current_tenant_id()
        
        # Obtener parámetros de consulta
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 100)), 100)  # Máximo 100 por página
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        sort_order = request.args.get('sort', 'newest')  # newest o oldest
        
        # Construir consulta base con más información
        query = """
            SELECT 
                a.id_afiliado, 
                a.nombre_completo as nombre, 
                a.email, 
                a.telefono, 
                a.ciudad, 
                a.fecha_registro, 
                a.estado, 
                a.experiencia,
                a.grado_academico,
                a.puntuacion as score,
                a.disponibilidad,
                a.cv_url,
                a.linkedin,
                a.portfolio,
                a.skills,
                a.comentarios,
                (SELECT COUNT(*) FROM Postulaciones p WHERE p.id_afiliado = a.id_afiliado) as total_aplicaciones,
                (SELECT GROUP_CONCAT(DISTINCT c.empresa SEPARATOR ', ') 
                 FROM Postulaciones p 
                 JOIN Vacantes v ON p.id_vacante = v.id_vacante 
                 JOIN Clientes c ON v.id_cliente = c.id_cliente 
                 WHERE p.id_afiliado = a.id_afiliado) as empresas_aplicadas
            FROM Afiliados a
            WHERE a.tenant_id = %s
        """
        params = [tenant_id]
        
        # Aplicar filtros
        if search:
            query += """ AND (
                nombre_completo LIKE %s OR 
                email LIKE %s OR 
                telefono LIKE %s OR
                ciudad LIKE %s OR
                experiencia LIKE %s
            )"""
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param, search_param])
        
        if status:
            query += " AND estado = %s"
            params.append(status)
        
        # Obtener total de registros
        count_query = query.replace("SELECT \n                a.id_afiliado, \n                a.nombre_completo as nombre, \n                a.email, \n                a.telefono, \n                a.ciudad, \n                a.fecha_registro, \n                a.estado, \n                a.experiencia,\n                a.grado_academico,\n                a.puntuacion as score,\n                a.disponibilidad,\n                a.cv_url,\n                a.linkedin,\n                a.portfolio,\n                a.skills,\n                a.comentarios,\n                (SELECT COUNT(*) FROM Postulaciones p WHERE p.id_afiliado = a.id_afiliado) as total_aplicaciones,\n                (SELECT GROUP_CONCAT(DISTINCT c.empresa SEPARATOR ', ') \n                 FROM Postulaciones p \n                 JOIN Vacantes v ON p.id_vacante = v.id_vacante \n                 JOIN Clientes c ON v.id_cliente = c.id_cliente \n                 WHERE p.id_afiliado = a.id_afiliado) as empresas_aplicadas", "SELECT COUNT(*) as total")
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Aplicar ordenación y paginación
        offset = (page - 1) * limit
        order_clause = "ORDER BY fecha_registro DESC" if sort_order == "newest" else "ORDER BY fecha_registro ASC"
        query += f" {order_clause} LIMIT {limit} OFFSET {offset}"
        
        cursor.execute(query, params)
        candidates = cursor.fetchall()
        
        # Cerrar cursor antes de devolver respuesta
        cursor.close()
        
        return jsonify({
            'success': True,
            'data': candidates,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error al obtener candidatos: {str(e)}")
        return jsonify({'error': 'Error al obtener la lista de candidatos'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

def create_candidate():
    """Crea un nuevo candidato."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        tenant_id = get_current_tenant_id()
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['nombre_completo', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'El campo {field} es requerido'}), 400
        
        # Verificar si ya existe un candidato con el mismo email
        cursor.execute("SELECT id_afiliado FROM Afiliados WHERE email = %s AND tenant_id = %s", 
                      (data['email'], tenant_id))
        if cursor.fetchone():
            return jsonify({'error': 'Ya existe un candidato con este email'}), 409
        
        # Insertar nuevo candidato
        sql = """
            INSERT INTO Afiliados (
                nombre_completo, email, telefono, ciudad, cargo_solicitado,
                experiencia, grado_academico, disponibilidad, cv_url,
                linkedin, portfolio, skills, comentarios, tenant_id, fecha_registro
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE())
        """
        
        cursor.execute(sql, (
            data['nombre_completo'],
            data['email'],
            data.get('telefono', ''),
            data.get('ciudad', ''),
            data.get('cargo_solicitado', ''),
            data.get('experiencia', ''),
            data.get('grado_academico', ''),
            data.get('disponibilidad', ''),
            data.get('cv_url', ''),
            data.get('linkedin', ''),
            data.get('portfolio', ''),
            data.get('skills', ''),
            data.get('comentarios', ''),
            tenant_id
        ))
        
        conn.commit()
        candidate_id = cursor.lastrowid
        
        return jsonify({
            'success': True,
            'message': 'Candidato creado exitosamente',
            'candidate': {
                'id': candidate_id,
                'nombre_completo': data['nombre_completo'],
                'email': data['email']
            }
        }), 201
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        app.logger.error(f"Error al crear candidato: {str(e)}")
        return jsonify({'error': 'Error al crear el candidato'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/candidates/<int:candidate_id>/profile', methods=['GET'])
@token_required
def get_candidate_profile(candidate_id):
    """Obtiene el perfil completo de un candidato con sus aplicaciones."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener información básica del candidato
        cursor.execute("""
            SELECT 
                a.id_afiliado, 
                a.nombre_completo as nombre, 
                a.email, 
                a.telefono, 
                a.ciudad, 
                a.fecha_registro, 
                a.estado, 
                a.experiencia,
                a.grado_academico,
                a.puntuacion as score,
                a.disponibilidad,
                a.cv_url,
                a.linkedin,
                a.portfolio,
                a.skills,
                a.comentarios,
                a.fecha_nacimiento,
                a.nacionalidad
            FROM Afiliados a
            WHERE a.id_afiliado = %s
        """, (candidate_id,))
        
        candidate = cursor.fetchone()
        if not candidate:
            return jsonify({"error": "Candidato no encontrado"}), 404
        
        # Obtener aplicaciones del candidato
        cursor.execute("""
            SELECT 
                p.id_postulacion,
                p.fecha_aplicacion,
                p.estado as estado_aplicacion,
                p.comentarios as comentarios_aplicacion,
                v.id_vacante,
                v.cargo_solicitado,
                v.salario,
                v.ciudad as ciudad_vacante,
                c.id_cliente,
                c.empresa,
                c.contacto
            FROM Postulaciones p
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            JOIN Clientes c ON v.id_cliente = c.id_cliente
            WHERE p.id_afiliado = %s
            ORDER BY p.fecha_aplicacion DESC
        """, (candidate_id,))
        
        applications = cursor.fetchall()
        
        # Obtener estadísticas
        cursor.execute("""
            SELECT 
                COUNT(*) as total_aplicaciones,
                COUNT(CASE WHEN p.estado = 'Contratado' THEN 1 END) as contratado,
                COUNT(CASE WHEN p.estado = 'Entrevista' THEN 1 END) as en_entrevista,
                COUNT(CASE WHEN p.estado = 'En Revisión' THEN 1 END) as en_revision,
                COUNT(CASE WHEN p.estado = 'Rechazado' THEN 1 END) as rechazado
            FROM Postulaciones p
            WHERE p.id_afiliado = %s
        """, (candidate_id,))
        
        stats = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'candidate': candidate,
                'applications': applications,
                'statistics': stats
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error al obtener perfil del candidato: {str(e)}")
        return jsonify({"error": "Error al obtener el perfil del candidato"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/candidates/search', methods=['GET'])
@token_required
def search_candidates():
    """
    Busca candidatos con filtros opcionales.
    
    Parámetros de consulta:
    - q: Término de búsqueda general (opcional)
    - tags: Lista de IDs de etiquetas separadas por comas (opcional)
    - registered_today: Si es 'true', solo devuelve candidatos registrados hoy (opcional)
    - status: Filtro por estado (opcional)
    - availability: Filtro por disponibilidad (opcional)
    - min_score: Puntuación mínima (opcional)
    - page: Número de página para paginación (por defecto: 1)
    - limit: Cantidad de resultados por página (por defecto: 10, máximo: 100)
    """
    try:
        # Obtener parámetros de la URL con valores por defecto
        term = request.args.get('q', '').strip()
        tags = request.args.get('tags', '')
        registered_today = request.args.get('registered_today', 'false').lower() == 'true'
        status = request.args.get('status')
        availability = request.args.get('availability')
        min_score = request.args.get('min_score')
        
        # Parámetros de paginación
        try:
            page = max(1, int(request.args.get('page', 1)))
            limit = min(100, max(1, int(request.args.get('limit', 10))))
            offset = (page - 1) * limit
        except ValueError:
            return jsonify({"error": "Los parámetros de paginación deben ser números válidos"}), 400
        
        # Llamar a la función interna con los argumentos de la URL
        results = _internal_search_candidates(
            term=term, 
            tags=tags, 
            registered_today=registered_today,
            status=status,
            availability=availability,
            min_score=min_score,
            limit=limit,
            offset=offset
        )
        
        # Contar el total de resultados (sin paginación) para la paginación
        total_results = len(_internal_search_candidates(
            term=term, 
            tags=tags, 
            registered_today=registered_today,
            status=status,
            availability=availability,
            min_score=min_score
        ))
        
        # Formatear la respuesta según lo esperado por la interfaz
        response = {
            "data": results,
            "pagination": {
                "total": total_results,
                "page": page,
                "limit": limit,
                "total_pages": (total_results + limit - 1) // limit
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f"Error en search_candidates: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "Error interno del servidor al buscar candidatos"}), 500


# ✨ SOLUCIÓN: Creamos el endpoint que faltaba
@app.route('/api/candidate/<int:candidate_id>/score', methods=['POST'])
@token_required
def update_candidate_score(candidate_id):
    """
    Actualiza la puntuación de un candidato y registra el cambio en el historial.
    
    Parámetros de entrada (JSON):
    - score: Puntuación a asignar (requerido, entre 0 y 100)
    - reason: Razón del cambio (opcional)
    
    Retorna:
    - 200: Puntuación actualizada correctamente
    - 400: Error en los datos de entrada
    - 404: Candidato no encontrado
    - 500: Error del servidor
    """
    try:
        # Obtener datos de la solicitud
        data = request.get_json()
        
        # Validar datos de entrada
        if not data or 'score' not in data:
            return jsonify({"error": "El campo 'score' es requerido"}), 400
            
        try:
            score = int(data['score'])
            if not (0 <= score <= 100):
                raise ValueError("La puntuación debe estar entre 0 y 100")
        except (ValueError, TypeError):
            return jsonify({"error": "La puntuación debe ser un número entero entre 0 y 100"}), 400
            
        reason = data.get('reason', '')
        user_id = get_jwt_identity()  # Obtener el ID del usuario autenticado
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Verificar que el candidato existe
            cursor.execute("SELECT id_afiliado FROM Afiliados WHERE id_afiliado = %s AND tenant_id = %s", (candidate_id, tenant_id))
            if not cursor.fetchone():
                return jsonify({"error": "Candidato no encontrado"}), 404
            
            # Iniciar transacción
            conn.start_transaction()
            
            # 1. Actualizar la puntuación en la tabla de afiliados
            cursor.execute(
                "UPDATE Afiliados SET puntuacion = %s, ultima_actualizacion = NOW() WHERE id_afiliado = %s",
                (score, candidate_id)
            )
            
            # 2. Registrar el cambio en el historial de puntuaciones
            cursor.execute(
                """
                INSERT INTO puntuaciones_candidato 
                (id_afiliado, puntuacion, motivo, usuario_id, fecha)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (candidate_id, score, reason, user_id)
            )
            
            # Confirmar transacción
            conn.commit()
            
            # Obtener datos actualizados del candidato para la respuesta
            cursor.execute(
                """
                SELECT a.id_afiliado as id, a.nombre_completo as name, a.puntuacion as score,
                       (SELECT MAX(fecha) FROM puntuaciones_candidato WHERE id_afiliado = %s) as last_updated
                FROM Afiliados a
                WHERE a.id_afiliado = %s
                """,
                (candidate_id, candidate_id)
            )
            
            result = cursor.fetchone()
            
            # Formatear fechas
            if result and 'last_updated' in result and result['last_updated']:
                if isinstance(result['last_updated'], (datetime, date)):
                    result['last_updated'] = result['last_updated'].isoformat()
            
            return jsonify({
                "message": "Puntuación actualizada correctamente",
                "data": result
            })
            
        except Exception as e:
            conn.rollback()
            app.logger.error(f"Error al actualizar puntuación: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({"error": "Error al actualizar la puntuación del candidato"}), 500
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error en update_candidate_score: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "Error interno del servidor"}), 500


@app.route('/api/candidate/<int:candidate_id>/interactions', methods=['POST'])
@token_required
def add_candidate_interaction(candidate_id):
    """
    Registra una interacción con un candidato.
    
    Parámetros de entrada (JSON):
    - type: Tipo de interacción (ej: 'llamada', 'email', 'entrevista', 'nota')
    - notes: Notas sobre la interacción (opcional)
    - scheduled_date: Fecha programada (opcional, para interacciones futuras)
    - status: Estado de la interacción (ej: 'completada', 'pendiente', 'cancelada')
    
    Retorna:
    - 201: Interacción registrada correctamente
    - 400: Error en los datos de entrada
    - 404: Candidato no encontrado
    - 500: Error del servidor
    """
    try:
        # Obtener datos de la solicitud
        data = request.get_json()
        
        # Validar datos de entrada
        if not data or 'type' not in data:
            return jsonify({"error": "El campo 'type' es requerido"}), 400
            
        interaction_type = data['type']
        notes = data.get('notes', '')
        status = data.get('status', 'completada')
        scheduled_date = data.get('scheduled_date')
        user_id = get_jwt_identity()  # Obtener el ID del usuario autenticado
        
        # Validar fechas
        scheduled_datetime = None
        if scheduled_date:
            try:
                scheduled_datetime = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return jsonify({"error": "Formato de fecha inválido. Use ISO 8601 (ej: 2023-01-01T12:00:00Z)"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Verificar que el candidato existe
            cursor.execute("SELECT id_afiliado, nombre_completo FROM Afiliados WHERE id_afiliado = %s AND tenant_id = %s", (candidate_id, tenant_id))
            candidate = cursor.fetchone()
            if not candidate:
                return jsonify({"error": "Candidato no encontrado"}), 404
            
            # Insertar la interacción
            cursor.execute(
                """
                INSERT INTO interacciones 
                (id_afiliado, tipo, notas, fecha, usuario_id, estado, fecha_programada)
                VALUES (%s, %s, %s, NOW(), %s, %s, %s)
                """,
                (candidate_id, interaction_type, notes, user_id, status, scheduled_datetime)
            )
            
            # Actualizar el último contacto del candidato
            cursor.execute(
                "UPDATE Afiliados SET ultimo_contacto = NOW() WHERE id_afiliado = %s",
                (candidate_id,)
            )
            
            conn.commit()
            
            # Obtener los datos de la interacción recién creada
            interaction_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT i.*, u.username as usuario_nombre
                FROM interacciones i
                LEFT JOIN users u ON i.usuario_id = u.id
                WHERE i.id = %s
                """,
                (interaction_id,)
            )
            
            interaction = cursor.fetchone()
            
            # Formatear fechas
            date_fields = ['fecha', 'fecha_programada', 'fecha_creacion', 'fecha_actualizacion']
            for field in date_fields:
                if field in interaction and interaction[field]:
                    if isinstance(interaction[field], (datetime, date)):
                        interaction[field] = interaction[field].isoformat()
            
            return jsonify({
                "message": "Interacción registrada correctamente",
                "data": interaction
            }), 201
            
        except Exception as e:
            conn.rollback()
            app.logger.error(f"Error al registrar interacción: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({"error": "Error al registrar la interacción"}), 500
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error en add_candidate_interaction: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "Error interno del servidor"}), 500


@app.route('/api/notifications', methods=['GET'])
@token_required
def get_notifications():
    """
    Devuelve notificaciones para el panel de control del CRM.
    Incluye notificaciones de nuevos candidatos, entrevistas, aplicaciones, etc.
    """
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de conexión"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        notifications = []
        
        # 1. Nuevos candidatos registrados hoy
        cursor.execute("""
            SELECT COUNT(*) as count FROM Afiliados 
            WHERE DATE(fecha_registro) = CURDATE()
        """)
        new_candidates = cursor.fetchone()['count']
        if new_candidates > 0:
            notifications.append({
                "id": "new_candidates_today",
                "type": "candidate",
                "title": f"Nuevos candidatos registrados",
                "message": f"{new_candidates} candidato(s) se registraron hoy",
                "timestamp": datetime.utcnow().isoformat(),
                "priority": "medium",
                "icon": "Users"
            })
        
        # 2. Entrevistas programadas para hoy
        cursor.execute("""
            SELECT COUNT(*) as count FROM Entrevistas 
            WHERE DATE(fecha_hora) = CURDATE() AND resultado = 'Programada'
        """)
        today_interviews = cursor.fetchone()['count']
        if today_interviews > 0:
            notifications.append({
                "id": "interviews_today",
                "type": "interview",
                "title": f"Entrevistas programadas para hoy",
                "message": f"{today_interviews} entrevista(s) programada(s) para hoy",
                "timestamp": datetime.utcnow().isoformat(),
                "priority": "high",
                "icon": "Calendar"
            })
        
        # 3. Nuevas aplicaciones pendientes
        cursor.execute("""
            SELECT COUNT(*) as count FROM Postulaciones p
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE p.estado = 'Pendiente' 
            AND DATE(p.fecha_aplicacion) = CURDATE()
        """)
        new_applications = cursor.fetchone()['count']
        if new_applications > 0:
            notifications.append({
                "id": "new_applications_today",
                "type": "application",
                "title": f"Nuevas aplicaciones",
                "message": f"{new_applications} nueva(s) aplicación(es) recibida(s) hoy",
                "timestamp": datetime.utcnow().isoformat(),
                "priority": "medium",
                "icon": "FileText"
            })
        
        # 4. Entrevistas sin resultado (más de 1 día)
        cursor.execute("""
            SELECT COUNT(*) as count FROM Entrevistas 
            WHERE fecha_hora < DATE_SUB(NOW(), INTERVAL 1 DAY) 
            AND resultado = 'Programada'
        """)
        overdue_interviews = cursor.fetchone()['count']
        if overdue_interviews > 0:
            notifications.append({
                "id": "overdue_interviews",
                "type": "interview",
                "title": f"Entrevistas pendientes de resultado",
                "message": f"{overdue_interviews} entrevista(s) sin resultado registrado",
                "timestamp": datetime.utcnow().isoformat(),
                "priority": "high",
                "icon": "AlertTriangle"
            })
        
        # 5. Vacantes con muchas aplicaciones
        cursor.execute("""
            SELECT v.cargo_solicitado, COUNT(p.id_postulacion) as aplicaciones
            FROM Vacantes v
            LEFT JOIN Postulaciones p ON v.id_vacante = p.id_vacante
            WHERE v.estado = 'Activa'
            GROUP BY v.id_vacante, v.cargo_solicitado
            HAVING aplicaciones >= 10
            ORDER BY aplicaciones DESC
        """)
        popular_vacancies = cursor.fetchall()
        for vacancy in popular_vacancies:
            notifications.append({
                "id": f"popular_vacancy_{vacancy['cargo_solicitado']}",
                "type": "vacancy",
                "title": f"Vacante popular: {vacancy['cargo_solicitado']}",
                "message": f"{vacancy['aplicaciones']} aplicaciones recibidas",
                "timestamp": datetime.utcnow().isoformat(),
                "priority": "low",
                "icon": "TrendingUp"
            })
        
        # Ordenar por prioridad y timestamp
        priority_order = {"high": 3, "medium": 2, "low": 1}
        notifications.sort(key=lambda x: (priority_order.get(x['priority'], 0), x['timestamp']), reverse=True)
        
        return jsonify(notifications)
        
    except Exception as e:
        app.logger.error(f"Error en get_notifications: {e}")
        return jsonify({"error": "Error al obtener notificaciones"}), 500
    finally:
        cursor.close()
        conn.close()





@app.route('/api/candidate/profile/<int:id_afiliado>', methods=['GET', 'PUT'])
@token_required
def handle_candidate_profile(id_afiliado):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de conexión"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        
        if request.method == 'GET':
            perfil = {"infoBasica": {}, "postulaciones": [], "entrevistas": [], "tags": []}
            cursor.execute("SELECT * FROM Afiliados WHERE id_afiliado = %s AND tenant_id = %s", (id_afiliado, tenant_id))
            perfil['infoBasica'] = cursor.fetchone()
            if not perfil['infoBasica']: return jsonify({"error": "Candidato no encontrado"}), 404
            
            cursor.execute("""
                SELECT P.id_postulacion, P.id_vacante, P.id_afiliado, P.fecha_aplicacion, P.estado, P.comentarios, V.cargo_solicitado, C.empresa 
                FROM Postulaciones P 
                JOIN Vacantes V ON P.id_vacante = V.id_vacante 
                JOIN Clientes C ON V.id_cliente = C.id_cliente 
                WHERE P.id_afiliado = %s AND V.id_cliente = %s
            """, (id_afiliado, tenant_id))
            perfil['postulaciones'] = cursor.fetchall()
            
            cursor.execute("""
                SELECT E.*, V.cargo_solicitado, C.empresa, P.id_afiliado 
                FROM Entrevistas E 
                JOIN Postulaciones P ON E.id_postulacion = P.id_postulacion 
                JOIN Vacantes V ON P.id_vacante = V.id_vacante 
                JOIN Clientes C ON V.id_cliente = C.id_cliente 
                WHERE P.id_afiliado = %s AND V.id_cliente = %s
            """, (id_afiliado, tenant_id))
            perfil['entrevistas'] = cursor.fetchall()
            
            cursor.execute("""
                SELECT T.id_tag, T.nombre_tag 
                FROM Afiliado_Tags AT 
                JOIN Tags T ON AT.id_tag = T.id_tag 
                WHERE AT.id_afiliado = %s AND T.id_cliente = %s
            """, (id_afiliado, tenant_id))
            perfil['tags'] = cursor.fetchall()
            return jsonify(perfil)
            
        elif request.method == 'PUT':
            data = request.get_json()
            update_fields = []
            params = []
            allowed_fields = ['nombre_completo', 'telefono', 'email', 'experiencia', 'ciudad', 'grado_academico', 'observaciones']
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    params.append(data[field])

            if not update_fields:
                return jsonify({"error": "No se proporcionaron campos para actualizar."}), 400

            params.append(id_afiliado)
            sql = f"UPDATE Afiliados SET {', '.join(update_fields)} WHERE id_afiliado = %s"
            cursor.execute(sql, tuple(params))
            conn.commit()
            return jsonify({"success": True, "message": "Perfil actualizado."})

    except Exception as e: return jsonify({"error": str(e)}), 500
    finally: cursor.close(); conn.close()

@app.route('/api/vacancies', methods=['GET', 'POST'])
@token_required
def handle_vacancies():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        
        if request.method == 'GET':
            estado = request.args.get('estado')
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 10))
            offset = (page - 1) * limit
            
            # Para administradores, mostrar todas las vacantes
            # Para otros usuarios, filtrar por tenant
            user_role = getattr(g, 'current_user', {}).get('rol', '')
            if user_role == 'Administrador':
                base_query = """
                    SELECT V.*, C.empresa, COUNT(P.id_postulacion) as aplicaciones 
                    FROM Vacantes V 
                    JOIN Clientes C ON V.id_cliente = C.id_cliente
                    LEFT JOIN Postulaciones P ON V.id_vacante = P.id_vacante
                    GROUP BY V.id_vacante, C.empresa
                """
                params = []
            else:
                base_query = """
                    SELECT V.*, C.empresa, COUNT(P.id_postulacion) as aplicaciones 
                    FROM Vacantes V 
                    JOIN Clientes C ON V.id_cliente = C.id_cliente
                    LEFT JOIN Postulaciones P ON V.id_vacante = P.id_vacante
                    WHERE V.id_cliente = %s
                    GROUP BY V.id_vacante, C.empresa
                """
                params = [tenant_id]
            
            if estado:
                base_query += " AND V.estado = %s"
                params.append(estado)
            
            # Contar total de resultados
            count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as count_table"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # Agregar paginación y ordenamiento
            base_query += " ORDER BY V.fecha_apertura DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(base_query, params)
            vacancies = cursor.fetchall()
            
            # Formatear respuesta según lo esperado por la interfaz
            response = {
                "data": vacancies,
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit
                }
            }
            
            return jsonify(response)
        elif request.method == 'POST':
            data = request.get_json()
            
            # Validar datos requeridos
            if not data.get('id_cliente'):
                return jsonify({"error": "El cliente es requerido"}), 400
            if not data.get('cargo_solicitado'):
                return jsonify({"error": "El cargo es requerido"}), 400
            if not data.get('ciudad'):
                return jsonify({"error": "La ciudad es requerida"}), 400
            
            id_cliente = data['id_cliente']
            
            # Verificar que el cliente pertenece al tenant actual
            cursor.execute("""
                SELECT id_cliente FROM Clientes 
                WHERE id_cliente = %s AND tenant_id = %s
            """, (id_cliente, tenant_id))
            
            if not cursor.fetchone():
                return jsonify({"error": "Cliente no válido o no pertenece a su organización"}), 400
            
            # Crear la vacante con el cliente seleccionado y el tenant actual
            sql = """
                INSERT INTO Vacantes (id_cliente, cargo_solicitado, ciudad, requisitos, salario, fecha_apertura, estado, tenant_id) 
                VALUES (%s, %s, %s, %s, %s, CURDATE(), 'Abierta', %s)
            """
            cursor.execute(sql, (id_cliente, data['cargo_solicitado'], data['ciudad'], data['requisitos'], data.get('salario'), tenant_id))
            conn.commit()
            
            # Obtener el ID de la vacante creada
            cursor.execute("SELECT LAST_INSERT_ID() as id_vacante")
            vacante_id = cursor.fetchone()['id_vacante']
            
            return jsonify({
                "success": True, 
                "message": "Vacante creada exitosamente.",
                "id_vacante": vacante_id
            }), 201
    except Exception as e: conn.rollback(); return jsonify({"error": str(e)}), 500
    finally: cursor.close(); conn.close()

@app.route('/api/vacancies/<int:id_vacante>/status', methods=['PUT'])
@token_required
def update_vacancy_status(id_vacante):
    data = request.get_json()
    nuevo_estado = data.get('estado')
    if not nuevo_estado: return jsonify({"error": "El nuevo estado es requerido"}), 400
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor()
    try:
        if nuevo_estado.lower() == 'cerrada':
            cursor.execute("UPDATE Vacantes SET estado = %s, fecha_cierre = CURDATE() WHERE id_vacante = %s", (nuevo_estado, id_vacante))
        else:
            cursor.execute("UPDATE Vacantes SET estado = %s WHERE id_vacante = %s", (nuevo_estado, id_vacante))
        conn.commit()
        return jsonify({"success": True, "message": f"Vacante actualizada a {nuevo_estado}."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# En app.py, reemplaza esta función completa
@app.route('/api/applications', methods=['GET','POST'])
@token_required
def handle_applications():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'GET':
            tenant_id = get_current_tenant_id()
            # Para administradores, mostrar todas las postulaciones
            # Para otros usuarios, filtrar por tenant a través de Vacantes
            user_role = getattr(g, 'current_user', {}).get('rol', '')
            
            # Consulta base
            base_sql = """
                SELECT p.id_postulacion, p.id_afiliado, p.id_vacante, p.fecha_aplicacion, p.estado, p.comentarios,
                       a.nombre_completo, 
                       v.cargo_solicitado, c.empresa, v.ciudad, v.id_cliente
                FROM Postulaciones p
                JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
                JOIN Vacantes v ON p.id_vacante = v.id_vacante
                JOIN Clientes c ON v.id_cliente = c.id_cliente
            """
            
            # Construir condiciones y parámetros
            conditions = []
            params = []
            
            # Filtrar por tenant si no es administrador
            if user_role != 'Administrador':
                conditions.append("v.tenant_id = %s")
                params.append(tenant_id)
            
            # Filtros adicionales
            if request.args.get('id_vacante'):
                conditions.append("p.id_vacante = %s")
                params.append(request.args.get('id_vacante'))
            if request.args.get('estado'):
                conditions.append("p.estado = %s")
                params.append(request.args.get('estado'))
            if request.args.get('fecha_inicio'):
                conditions.append("p.fecha_aplicacion >= %s")
                params.append(request.args.get('fecha_inicio'))
            
            # Agregar WHERE si hay condiciones
            if conditions:
                base_sql += " WHERE " + " AND ".join(conditions)
            
            base_sql += " ORDER BY p.fecha_aplicacion DESC"
            cursor.execute(base_sql, tuple(params))
            # Convertir fechas para que sean compatibles con JSON
            results = cursor.fetchall()
            for row in results:
                for key, value in row.items():
                    if isinstance(value, (datetime, date)):
                        row[key] = value.isoformat()
            return jsonify(results)
        
        elif request.method == 'POST':
            data = request.get_json()
            
            # Debug: Log received data
            print(f"DEBUG: Received application data: {data}")
            
            # Verificar que el afiliado y la vacante existen
            cursor.execute("SELECT id_afiliado FROM Afiliados WHERE id_afiliado = %s", (data['id_afiliado'],))
            if not cursor.fetchone():
                return jsonify({"success": False, "message": "Afiliado no encontrado"}), 404
                
            cursor.execute("SELECT id_vacante FROM Vacantes WHERE id_vacante = %s", (data['id_vacante'],))
            if not cursor.fetchone():
                return jsonify({"success": False, "message": "Vacante no encontrada"}), 404
            
            # Verificar si ya existe la postulación
            cursor.execute("SELECT id_postulacion FROM Postulaciones WHERE id_afiliado = %s AND id_vacante = %s", (data['id_afiliado'], data['id_vacante']))
            existing = cursor.fetchone()
            if existing: 
                print(f"DEBUG: Postulación ya existe: {existing}")
                return jsonify({"success": False, "message": "Este candidato ya ha postulado a esta vacante."}), 409
            
            # Insertar la nueva postulación
            sql = "INSERT INTO Postulaciones (id_afiliado, id_vacante, fecha_aplicacion, estado, comentarios) VALUES (%s, %s, NOW(), 'Recibida', %s)"
            cursor.execute(sql, (data['id_afiliado'], data['id_vacante'], data.get('comentarios', '')))
            new_postulation_id = cursor.lastrowid
            conn.commit()

            cursor.execute("""
                SELECT a.telefono, a.nombre_completo, v.cargo_solicitado, v.ciudad, v.salario, v.requisitos
                FROM Afiliados a, Vacantes v WHERE a.id_afiliado = %s AND v.id_vacante = %s
            """, (data['id_afiliado'], data['id_vacante']))
            info = cursor.fetchone()

            if info and info.get('telefono'):
                # Convertir Decimal a float si existe
                salario_val = info.get('salario')
                salario_str = f"L. {float(salario_val):,.2f}" if salario_val else "No especificado"
                message_body = (
                    f"¡Hola {info['nombre_completo'].split(' ')[0]}! Te saluda Henmir. 👋\n\n"
                    f"Hemos considerado tu perfil para una nueva oportunidad laboral y te hemos postulado a la siguiente vacante:\n\n"
                    f"📌 *Puesto:* {info['cargo_solicitado']}\n"
                    f"📍 *Ubicación:* {info['ciudad']}\n"
                    f"💰 *Salario:* {salario_str}\n\n"
                    f"*Requisitos principales:*\n{info['requisitos']}\n\n"
                    "Por favor, confirma si estás interesado/a en continuar con este proceso. ¡Mucho éxito!"
                )
                
                # Notificaciones WhatsApp temporalmente deshabilitadas
                # TODO: Configurar Redis/Celery para habilitar notificaciones
                app.logger.info(f"Notificación WhatsApp deshabilitada - Candidato: {info['nombre_completo']}, Teléfono: {info['telefono']}")
                
                return jsonify({
                    "success": True, 
                    "message": "Postulación registrada exitosamente. (Notificaciones WhatsApp temporalmente deshabilitadas)", 
                    "id_postulacion": new_postulation_id,
                    "notification_status": "disabled"
                }), 201
            
            return jsonify({"success": True, "message": "Postulación registrada (candidato sin teléfono para notificar).", "id_postulacion": new_postulation_id}), 201
            
    except Exception as e: 
        conn.rollback(); import traceback; traceback.print_exc(); return jsonify({"success": False, "error": str(e)}), 500
    finally: 
        cursor.close(); conn.close()


@app.route('/api/applications/<int:id_postulacion>', methods=['DELETE'])
@token_required
def delete_application(id_postulacion):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor()
    try:
        tenant_id = get_current_tenant_id()
        
        # Verificar que la postulación pertenece al tenant
        cursor.execute("SELECT id_postulacion FROM Postulaciones WHERE id_postulacion = %s AND tenant_id = %s", (id_postulacion, tenant_id))
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Postulación no encontrada."}), 404
        
        # Antes de borrar la postulación, borramos las entrevistas asociadas si existen
        cursor.execute("DELETE FROM Entrevistas WHERE id_postulacion = %s", (id_postulacion,))
        
        # Ahora borramos la postulación
        cursor.execute("DELETE FROM Postulaciones WHERE id_postulacion = %s AND tenant_id = %s", (id_postulacion, tenant_id))
        
        conn.commit()
        return jsonify({"success": True, "message": "Postulación eliminada correctamente."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# AÑADE esta nueva función justo después de 'delete_application' en app.py

@app.route('/api/applications/<int:id_postulacion>/comments', methods=['PUT'])
@token_required
def update_application_comments(id_postulacion):
    data = request.get_json()
    nuevos_comentarios = data.get('comentarios', '') # Aceptamos comentarios vacíos

    if 'comentarios' not in data:
        return jsonify({"success": False, "error": "El campo 'comentarios' es requerido."}), 400

    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor()
    try:
        sql = "UPDATE Postulaciones SET comentarios = %s WHERE id_postulacion = %s"
        cursor.execute(sql, (nuevos_comentarios, id_postulacion))

        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"success": False, "error": f"No se encontró una postulación con el ID {id_postulacion}."}), 404

        conn.commit()
        return jsonify({"success": True, "message": "Comentarios de la postulación actualizados."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": f"Error inesperado al actualizar comentarios: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()



# En app.py, reemplaza esta función completa
@app.route('/api/interviews', methods=['GET', 'POST'])
@token_required
def handle_interviews():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        
        if request.method == 'GET':
            sql = """
                SELECT e.id_entrevista, e.fecha_hora, e.entrevistador, e.resultado, e.observaciones,
                       p.id_afiliado, a.nombre_completo, v.cargo_solicitado, v.id_vacante, c.empresa
                FROM Entrevistas e
                JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
                JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
                JOIN Vacantes v ON p.id_vacante = v.id_vacante
                JOIN Clientes c ON v.id_cliente = c.id_cliente
            """
            conditions = []
            params = []
            if request.args.get('vacante_id'):
                conditions.append("v.id_vacante = %s")
                params.append(request.args.get('vacante_id'))
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY e.fecha_hora DESC"
            cursor.execute(sql, tuple(params))
            results = cursor.fetchall()
            for row in results:
                if isinstance(row.get('fecha_hora'), (datetime, date)):
                    row['fecha_hora'] = row['fecha_hora'].isoformat()
            return jsonify(results)

        elif request.method == 'POST':
            data = request.get_json()
            id_postulacion = data.get('id_postulacion')
            fecha_hora_str = data.get('fecha_hora')
            entrevistador = data.get('entrevistador')
            observaciones = data.get('observaciones', '')

            if not all([id_postulacion, fecha_hora_str, entrevistador]):
                return jsonify({"success": False, "error": "Faltan datos requeridos."}), 400

            try:
                # Verificar que la postulación pertenece al tenant
                cursor.execute("SELECT id_postulacion FROM Postulaciones WHERE id_postulacion = %s AND tenant_id = %s", (id_postulacion, tenant_id))
                if not cursor.fetchone():
                    return jsonify({"success": False, "error": "Postulación no encontrada."}), 404
                
                sql_insert = "INSERT INTO Entrevistas (id_postulacion, fecha_hora, entrevistador, resultado, observaciones, id_cliente) VALUES (%s, %s, %s, 'Programada', %s, %s)"
                cursor.execute(sql_insert, (id_postulacion, fecha_hora_str, entrevistador, observaciones, tenant_id))
                new_interview_id = cursor.lastrowid
                
                cursor.execute("UPDATE Postulaciones SET estado = 'En Entrevista' WHERE id_postulacion = %s", (id_postulacion,))
                conn.commit()

                cursor.execute("""
                    SELECT a.telefono, a.nombre_completo, v.cargo_solicitado, c.empresa FROM Postulaciones p
                    JOIN Afiliados a ON p.id_afiliado = a.id_afiliado JOIN Vacantes v ON p.id_vacante = v.id_vacante JOIN Clientes c ON v.id_cliente = c.id_cliente
                    WHERE p.id_postulacion = %s
                """, (id_postulacion,))
                info = cursor.fetchone()

                if info and info.get('telefono'):
                    fecha_obj = datetime.fromisoformat(fecha_hora_str)
                    fecha_formateada = fecha_obj.strftime('%A, %d de %B de %Y a las %I:%M %p')
                    message_body = (
                        f"¡Buenas noticias, {info['nombre_completo'].split(' ')[0]}! 🎉\n\n"
                        f"Hemos agendado tu entrevista para la vacante de *{info['cargo_solicitado']}* en la empresa *{info['empresa']}*.\n\n"
                        f"🗓️ *Fecha y Hora:* {fecha_formateada}\n👤 *Entrevistador(a):* {entrevistador}\n\n*Detalles adicionales:*\n{observaciones}\n\n"
                        "Por favor, sé puntual. ¡Te deseamos mucho éxito en tu entrevista!"
                    )
                    
                    # Notificaciones WhatsApp temporalmente deshabilitadas
                    app.logger.info(f"Notificación WhatsApp deshabilitada para entrevista - Candidato: {info['nombre_completo']}")
                    
                    return jsonify({
                        "success": True, 
                        "message": "Entrevista agendada exitosamente. (Notificaciones WhatsApp temporalmente deshabilitadas)", 
                        "id_entrevista": new_interview_id,
                        "notification_status": "disabled"
                    }), 201
                
                return jsonify({"success": True, "message": "Entrevista agendada."}), 201
            
            except mysql.connector.Error as err:
                conn.rollback()
                if err.errno == 1452: return jsonify({"success": False, "error": f"La postulación con ID {id_postulacion} no existe."}), 404
                return jsonify({"success": False, "error": f"Error de base de datos: {str(err)}"}), 500
            except Exception as e: 
                conn.rollback()
                return jsonify({"success": False, "error": str(e)}), 500
    finally: 
        cursor.close()
        conn.close()


@app.route('/api/interviews/stats', methods=['GET'])
@token_required
def get_interview_stats():
    """
    Devuelve estadísticas de entrevistas por período para el calendario.
    Incluye entrevistas programadas, completadas, canceladas, etc.
    """
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de conexión"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        estado = request.args.get('estado')
        
        # Construir consulta base
        sql = """
            SELECT 
                e.id_entrevista,
                e.fecha_hora,
                e.entrevistador,
                e.resultado,
                e.observaciones,
                a.nombre_completo as candidate_name,
                a.telefono as candidate_phone,
                a.email as candidate_email,
                v.cargo_solicitado as position,
                c.empresa as company,
                p.id_postulacion,
                p.estado as application_status
            FROM Entrevistas e
            JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
            JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            JOIN Clientes c ON v.id_cliente = c.id_cliente
        """
        
        params = []
        conditions = []
        
        # Aplicar filtros
        if fecha_desde:
            conditions.append("DATE(e.fecha_hora) >= %s")
            params.append(fecha_desde)
            
        if fecha_hasta:
            conditions.append("DATE(e.fecha_hora) <= %s")
            params.append(fecha_hasta)
            
        if estado:
            conditions.append("e.resultado = %s")
            params.append(estado)
            
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        sql += " ORDER BY e.fecha_hora DESC"
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        # Formatear fechas y agregar información adicional
        for row in results:
            if isinstance(row.get('fecha_hora'), (datetime, date)):
                row['fecha_hora'] = row['fecha_hora'].isoformat()
                row['fecha'] = row['fecha_hora'].split('T')[0]
                row['hora'] = row['fecha_hora'].split('T')[1][:5]
            
            # Agregar tipo de entrevista basado en el resultado
            if row['resultado'] == 'Programada':
                row['type'] = 'interview'
                row['status'] = 'scheduled'
            elif row['resultado'] in ['Contratado', 'Aprobado']:
                row['type'] = 'interview'
                row['status'] = 'completed'
            else:
                row['type'] = 'interview'
                row['status'] = 'completed'
                
            # Agregar información de ubicación (virtual por defecto)
            row['isVirtual'] = True
            row['location'] = None
            
        return jsonify(results)
        
    except Exception as e:
        app.logger.error(f"Error en get_interview_stats: {e}")
        return jsonify({"error": "Error al obtener estadísticas de entrevistas"}), 500
    finally: 
        cursor.close()
        conn.close()


@app.route('/api/hired', methods=['GET', 'POST'])
@token_required
def handle_hired():
    try:
        conn = get_db_connection()
        if not conn: 
            app.logger.error("Error de conexión a BD en /api/hired")
            return jsonify({"error": "Error de BD"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'GET':
            app.logger.info("Obteniendo lista de contratados")
            sql = """
                SELECT 
                    co.id_contratado, co.fecha_contratacion, co.salario_final,
                    IFNULL(co.tarifa_servicio, 0) as tarifa_servicio, 
                    IFNULL(co.monto_pagado, 0) as monto_pagado,
                    (IFNULL(co.tarifa_servicio, 0) - IFNULL(co.monto_pagado, 0)) AS saldo_pendiente,
                    a.id_afiliado, a.nombre_completo, v.cargo_solicitado, c.empresa
                FROM Contratados co
                JOIN Afiliados a ON co.id_afiliado = a.id_afiliado
                JOIN Vacantes v ON co.id_vacante = v.id_vacante
                JOIN Clientes c ON v.id_cliente = c.id_cliente
                ORDER BY saldo_pendiente DESC, co.fecha_contratacion DESC;
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            
            # Procesar resultados
            for row in results:
                if isinstance(row.get('fecha_contratacion'), (datetime, date)):
                    row['fecha_contratacion'] = row['fecha_contratacion'].isoformat()
                for key, value in row.items():
                    if isinstance(value, Decimal):
                        row[key] = float(value)
            
            app.logger.info(f"Retornando {len(results)} contratados")
            return jsonify(results)
            
    except Exception as e:
        app.logger.error(f"Error en /api/hired: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

        elif request.method == 'POST':
            data = request.get_json()
            id_afiliado = data.get('id_afiliado')
            id_vacante = data.get('id_vacante')

            if not all([id_afiliado, id_vacante]):
                 return jsonify({"success": False, "error": "Faltan id_afiliado o id_vacante."}), 400
            
            try:
                # Verificar que el afiliado y vacante pertenecen al tenant
                cursor.execute("SELECT id_afiliado FROM Afiliados WHERE id_afiliado = %s", (id_afiliado,))
                if not cursor.fetchone():
                    return jsonify({"success": False, "error": "Afiliado no encontrado."}), 404
                
                cursor.execute("SELECT id_vacante FROM Vacantes WHERE id_vacante = %s AND tenant_id = %s", (id_vacante, tenant_id))
                if not cursor.fetchone():
                    return jsonify({"success": False, "error": "Vacante no encontrada."}), 404
                
                sql_insert = "INSERT INTO Contratados (id_afiliado, id_vacante, fecha_contratacion, salario_final, tarifa_servicio, tenant_id) VALUES (%s, %s, CURDATE(), %s, %s, %s)"
                cursor.execute(sql_insert, (id_afiliado, id_vacante, data.get('salario_final'), data.get('tarifa_servicio'), tenant_id))
                new_hired_id = cursor.lastrowid
                
                cursor.execute("UPDATE Postulaciones SET estado = 'Contratado' WHERE id_afiliado = %s AND id_vacante = %s AND tenant_id = %s", (id_afiliado, id_vacante, tenant_id))
                conn.commit()

                cursor.execute("""
                    SELECT a.telefono, a.nombre_completo, v.cargo_solicitado, c.empresa
                    FROM Afiliados a, Vacantes v, Clientes c
                    WHERE a.id_afiliado = %s AND v.id_vacante = %s AND v.id_cliente = c.id_cliente
                """, (id_afiliado, id_vacante))
                info = cursor.fetchone()

                if info and info.get('telefono'):
                    message_body = (
                        f"¡FELICIDADES, {info['nombre_completo'].split(' ')[0]}! 🥳\n\n"
                        f"Nos complace enormemente informarte que has sido **CONTRATADO/A** para el puesto de *{info['cargo_solicitado']}* en la empresa *{info['empresa']}*.\n\n"
                        "Este es un gran logro y el resultado de tu excelente desempeño en el proceso de selección. En breve, el equipo de recursos humanos de la empresa se pondrá en contacto contigo para coordinar los siguientes pasos.\n\n"
                        "De parte de todo el equipo de Henmir, ¡te deseamos el mayor de los éxitos en tu nuevo rol!"
                    )
                    
                    # Notificaciones WhatsApp temporalmente deshabilitadas
                    app.logger.info(f"Notificación WhatsApp deshabilitada para contratación - Candidato: {info['nombre_completo']}")
                    
                    return jsonify({
                        "success": True, 
                        "message": "Candidato contratado exitosamente. (Notificaciones WhatsApp temporalmente deshabilitadas)", 
                        "id_contratado": new_hired_id,
                        "notification_status": "disabled"
                    }), 201

                return jsonify({"success": True, "message": "Candidato registrado como contratado."}), 201

            except mysql.connector.Error as err:
                conn.rollback()
                if err.errno == 1062: return jsonify({"success": False, "error": "Este candidato ya ha sido registrado como contratado para esta vacante."}), 409
                return jsonify({"success": False, "error": f"Error de base de datos: {str(err)}"}), 500
            except Exception as e: 
                conn.rollback()
                return jsonify({"success": False, "error": str(e)}), 500    

@app.route('/api/hired/<int:id_contratado>/payment', methods=['POST'])
@token_required
def register_payment(id_contratado):
    data = request.get_json()
    monto_pago = data.get('monto')

    if not monto_pago:
        return jsonify({"success": False, "error": "El monto del pago es requerido."}), 400
    
    try:
        monto_float = float(monto_pago)
        if monto_float <= 0:
            return jsonify({"success": False, "error": "El monto del pago debe ser un número positivo."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "El monto del pago debe ser un número válido."}), 400

    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor()
    try:
        tenant_id = get_current_tenant_id()
        
        # Usamos una actualización atómica para evitar problemas de concurrencia
        sql = "UPDATE Contratados SET monto_pagado = monto_pagado + %s WHERE id_contratado = %s AND id_cliente = %s"
        cursor.execute(sql, (monto_float, id_contratado, tenant_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": "No se encontró el registro de contratación."}), 404

        return jsonify({"success": True, "message": "Pago registrado correctamente."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()




@app.route('/api/hired/<int:id_contratado>', methods=['DELETE'])
@token_required
def annul_hiring(id_contratado):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Error de BD"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        tenant_id = get_current_tenant_id()
        
        # Primero, obtenemos los IDs necesarios antes de borrar
        cursor.execute("SELECT id_afiliado, id_vacante FROM Contratados WHERE id_contratado = %s AND tenant_id = %s", (id_contratado, tenant_id))
        record = cursor.fetchone()
        if not record:
            return jsonify({"success": False, "error": "Registro de contratación no encontrado."}), 404

        # Segundo, borramos el registro de la tabla Contratados
        cursor.execute("DELETE FROM Contratados WHERE id_contratado = %s AND tenant_id = %s", (id_contratado, tenant_id))
        
        # Tercero, revertimos el estado de la postulación a 'Oferta' o el estado anterior que consideres
        cursor.execute("UPDATE Postulaciones SET estado = 'Oferta' WHERE id_afiliado = %s AND id_vacante = %s AND tenant_id = %s", (record['id_afiliado'], record['id_vacante'], tenant_id))
        
        conn.commit()
        return jsonify({"success": True, "message": "Contratación anulada correctamente."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()




@app.route('/api/clients', methods=['GET', 'POST'])
@token_required
def handle_clients():
    try:
        conn = get_db_connection()
        if not conn: 
            app.logger.error("Error de conexión a BD en /api/clients")
            return jsonify({"error": "Error de BD"}), 500
        
        cursor = conn.cursor(dictionary=True)
        tenant_id = get_current_tenant_id()
        
        if request.method == 'GET':
            app.logger.info("Obteniendo lista de clientes")
            cursor.execute("SELECT * FROM Clientes WHERE tenant_id = %s ORDER BY empresa", (tenant_id,))
            results = cursor.fetchall()
            app.logger.info(f"Retornando {len(results)} clientes")
            return jsonify(results)
        elif request.method == 'POST':
            data = request.get_json()
            sql = "INSERT INTO Clientes (empresa, contacto_nombre, telefono, email, sector, observaciones, tenant_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (data['empresa'], data['contacto_nombre'], data['telefono'], data['email'], data['sector'], data['observaciones'], tenant_id))
            conn.commit()
            return jsonify({"success": True, "message": "Cliente agregado."}), 201
            
    except Exception as e:
        app.logger.error(f"Error en /api/clients: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/clients/<int:client_id>/metrics', methods=['GET'])
@token_required
def get_client_metrics(client_id):
    conn = get_db_connection()
    if not conn: 
        app.logger.error("Error de conexión a BD en /api/clients/metrics")
        return jsonify({"error": "Error de BD"}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        app.logger.info(f"Obteniendo métricas para cliente {client_id}")
        
        # Verificar que el cliente existe
        cursor.execute("SELECT id_cliente FROM Clientes WHERE id_cliente = %s AND tenant_id = %s", (client_id, tenant_id))
        if not cursor.fetchone():
            return jsonify({"error": "Cliente no encontrado"}), 404
        
        # Métricas básicas
        sql = """
            SELECT 
                COUNT(DISTINCT v.id_vacante) as total_vacancies,
                COUNT(DISTINCT CASE WHEN v.estado = 'Abierta' THEN v.id_vacante END) as open_vacancies,
                COUNT(DISTINCT CASE WHEN v.estado = 'Cerrada' THEN v.id_vacante END) as closed_vacancies,
                COUNT(DISTINCT p.id_postulacion) as total_applications,
                COUNT(DISTINCT co.id_contratado) as hired_candidates,
                CASE 
                    WHEN COUNT(DISTINCT p.id_postulacion) > 0 THEN 
                        (COUNT(DISTINCT co.id_contratado) * 100.0 / COUNT(DISTINCT p.id_postulacion))
                    ELSE 0 
                END as conversion_rate
            FROM Clientes c
            LEFT JOIN Vacantes v ON c.id_cliente = v.id_cliente AND v.tenant_id = %s
            LEFT JOIN Postulaciones p ON v.id_vacante = p.id_vacante AND p.tenant_id = %s
            LEFT JOIN Contratados co ON v.id_vacante = co.id_vacante AND co.tenant_id = %s
            WHERE c.id_cliente = %s AND c.tenant_id = %s
        """
        cursor.execute(sql, (tenant_id, tenant_id, tenant_id, client_id, tenant_id))
        metrics = cursor.fetchone()
        
        # Tiempo promedio de contratación
        avg_hiring_time_sql = """
            SELECT AVG(DATEDIFF(co.fecha_contratacion, v.fecha_apertura)) as avg_hiring_time
            FROM Contratados co
            JOIN Vacantes v ON co.id_vacante = v.id_vacante
            WHERE v.id_cliente = %s AND co.fecha_contratacion IS NOT NULL
        """
        cursor.execute(avg_hiring_time_sql, (client_id,))
        avg_time = cursor.fetchone()
        
        # Ingresos totales (si aplica)
        revenue_sql = """
            SELECT SUM(COALESCE(co.tarifa_servicio, 0)) as total_revenue
            FROM Contratados co
            JOIN Vacantes v ON co.id_vacante = v.id_vacante
            WHERE v.id_cliente = %s
        """
        cursor.execute(revenue_sql, (client_id,))
        revenue = cursor.fetchone()
        
        result = {
            "totalVacancies": metrics['total_vacancies'] or 0,
            "openVacancies": metrics['open_vacancies'] or 0,
            "closedVacancies": metrics['closed_vacancies'] or 0,
            "totalApplications": metrics['total_applications'] or 0,
            "hiredCandidates": metrics['hired_candidates'] or 0,
            "conversionRate": float(metrics['conversion_rate'] or 0),
            "averageHiringTime": int(avg_time['avg_hiring_time'] or 0),
            "totalRevenue": float(revenue['total_revenue'] or 0) if revenue['total_revenue'] else None
        }
        
        app.logger.info(f"Métricas calculadas para cliente {client_id}: {result}")
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error en /api/clients/metrics: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ===============================================================
# SECCIÓN 7: GESTIÓN DE USUARIOS Y AUTENTICACIÓN
# ===============================================================

def get_user_by_id(user_id):
    """Obtiene un usuario por su ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.*, r.nombre as rol_nombre, r.permisos 
            FROM Users u 
            LEFT JOIN Roles r ON u.rol_id = r.id 
            WHERE u.id = %s
        """, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            # Convertir los permisos de JSON string a diccionario si existe
            if user.get('permisos') and isinstance(user['permisos'], str):
                try:
                    user['permisos'] = json.loads(user['permisos'])
                except json.JSONDecodeError:
                    user['permisos'] = {}
        
        return user
    except Exception as e:
        app.logger.error(f"Error al obtener usuario por ID: {str(e)}")
        return None

def get_user_by_email(email):
    """Obtiene un usuario por su email."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.*, r.nombre as rol_nombre, r.permisos 
            FROM Users u 
            LEFT JOIN Roles r ON u.rol_id = r.id 
            WHERE u.email = %s
        """, (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and user.get('permisos') and isinstance(user['permisos'], str):
            try:
                user['permisos'] = json.loads(user['permisos'])
            except json.JSONDecodeError:
                user['permisos'] = {}
                
        return user
    except Exception as e:
        app.logger.error(f"Error al obtener usuario por email: {str(e)}")
        return None

def create_user(user_data):
    """Crea un nuevo usuario."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el email ya existe
        cursor.execute("SELECT id FROM Users WHERE email = %s", (user_data['email'],))
        if cursor.fetchone():
            return {'error': 'El correo electrónico ya está registrado'}, 400
            
        # Hashear la contraseña
        hashed_password = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt())
        
        # Insertar el nuevo usuario
        cursor.execute("""
            INSERT INTO Users (nombre, email, password, telefono, rol_id, activo, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (
            user_data.get('nombre'),
            user_data['email'],
            hashed_password.decode('utf-8'),
            user_data.get('telefono'),
            user_data.get('rol_id', 2),  # Por defecto rol de usuario estándar
            user_data.get('activo', True)
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        # Obtener el usuario recién creado
        user = get_user_by_id(user_id)
        
        cursor.close()
        conn.close()
        
        return user, 201
    except Exception as e:
        app.logger.error(f"Error al crear usuario: {str(e)}")
        return {'error': 'Error interno del servidor'}, 500

def update_user(user_id, user_data):
    """Actualiza un usuario existente."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el usuario existe
        cursor.execute("SELECT id FROM Users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return {'error': 'Usuario no encontrado'}, 404
            
        # Si se está actualizando el email, verificar que no esté en uso
        if 'email' in user_data:
            cursor.execute("SELECT id FROM Users WHERE email = %s AND id != %s", 
                         (user_data['email'], user_id))
            if cursor.fetchone():
                return {'error': 'El correo electrónico ya está en uso'}, 400
        
        # Preparar la consulta de actualización
        update_fields = []
        params = []
        
        if 'nombre' in user_data:
            update_fields.append("nombre = %s")
            params.append(user_data['nombre'])
            
        if 'email' in user_data:
            update_fields.append("email = %s")
            params.append(user_data['email'])
            
        if 'password' in user_data and user_data['password']:
            hashed_password = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt())
            update_fields.append("password = %s")
            params.append(hashed_password.decode('utf-8'))
            
        if 'telefono' in user_data:
            update_fields.append("telefono = %s")
            params.append(user_data['telefono'])
            
        if 'rol_id' in user_data:
            update_fields.append("rol_id = %s")
            params.append(user_data['rol_id'])
            
        if 'activo' in user_data:
            update_fields.append("activo = %s")
            params.append(user_data['activo'])
        
        # Si no hay campos para actualizar, retornar error
        if not update_fields:
            return {'error': 'No se proporcionaron datos para actualizar'}, 400
            
        # Agregar el ID al final de los parámetros
        params.append(user_id)
        
        # Construir y ejecutar la consulta
        update_query = f"UPDATE Users SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(update_query, params)
        conn.commit()
        
        # Obtener el usuario actualizado
        user = get_user_by_id(user_id)
        
        cursor.close()
        conn.close()
        
        return user
    except Exception as e:
        app.logger.error(f"Error al actualizar usuario: {str(e)}")
        return {'error': 'Error interno del servidor'}, 500

def delete_user(user_id):
    """Elimina un usuario (borrado lógico)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si el usuario existe
        cursor.execute("SELECT id FROM Users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return {'error': 'Usuario no encontrado'}, 404
            
        # Realizar borrado lógico
        cursor.execute("UPDATE Users SET activo = FALSE, fecha_eliminacion = NOW() WHERE id = %s", (user_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {'message': 'Usuario eliminado correctamente'}
    except Exception as e:
        app.logger.error(f"Error al eliminar usuario: {str(e)}")
        return {'error': 'Error interno del servidor'}, 500

def get_all_roles():
    """Obtiene todos los roles disponibles."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id, nombre, descripcion, permisos FROM Roles WHERE activo = TRUE")
        roles = cursor.fetchall()
        
        # Convertir permisos de JSON string a diccionario
        for role in roles:
            if role.get('permisos') and isinstance(role['permisos'], str):
                try:
                    role['permisos'] = json.loads(role['permisos'])
                except json.JSONDecodeError:
                    role['permisos'] = {}
        
        cursor.close()
        conn.close()
        
        return roles
    except Exception as e:
        app.logger.error(f"Error al obtener roles: {str(e)}")
        return []

def log_user_activity(user_id, action, details=None, ip_address=None, user_agent=None):
    """
    Registra una actividad de usuario en el sistema.
    
    Args:
        user_id (int): ID del usuario que realiza la acción
        action (str): Tipo de acción realizada (ej: 'user_login', 'user_updated')
        details (dict, optional): Detalles adicionales de la acción
        ip_address (str, optional): Dirección IP del usuario
        user_agent (str, optional): User-Agent del navegador del usuario
        
    Returns:
        bool: True si el registro fue exitoso, False en caso contrario
    """
    if not user_id or not action:
        app.logger.error("No se pudo registrar la actividad: faltan parámetros requeridos")
        return False
        
    try:
        # Obtener información adicional de la solicitud si no se proporciona
        if not ip_address and hasattr(request, 'remote_addr'):
            ip_address = request.remote_addr
            
        if not user_agent and hasattr(request, 'user_agent'):
            user_agent = str(request.user_agent)
        
        # Preparar los detalles para el registro
        log_details = {
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'ip_address': ip_address,
            **(details if isinstance(details, dict) else {'data': details})
        }
        
        # Conectar a la base de datos
        conn = get_db_connection()
        if not conn:
            app.logger.error("No se pudo conectar a la base de datos para registrar actividad")
            return False
            
        cursor = conn.cursor()
        
        # Insertar el registro de actividad
        cursor.execute("""
            INSERT INTO UserActivityLog 
            (user_id, activity_type, description, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id, 
            action, 
            json.dumps(log_details, ensure_ascii=False, default=str),
            ip_address[:45] if ip_address else None,  # Limitar longitud para la columna
            user_agent[:255] if user_agent else None  # Limitar longitud para la columna
        ))
        
        conn.commit()
        
        # También registrar en el log de la aplicación
        app.logger.info(
            f"Actividad de usuario - UserID: {user_id}, "
            f"Acción: {action}, "
            f"IP: {ip_address}"
        )
        
        return True
        
    except Exception as e:
        # Registrar el error tanto en el log de la aplicación como en la consola
        error_msg = f"Error al registrar actividad de usuario: {str(e)}"
        app.logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}")
        
        # Intentar registrar el error en la base de datos si es posible
        try:
            if 'conn' in locals() and conn:
                error_details = {
                    'error': str(e),
                    'action': action,
                    'user_id': user_id,
                    'original_details': details
                }
                cursor.execute("""
                    INSERT INTO ErrorLogs 
                    (error_type, error_message, stack_trace)
                    VALUES (%s, %s, %s)
                """, (
                    'activity_log_error',
                    'Error al registrar actividad de usuario',
                    json.dumps(error_details, default=str)
                ))
                conn.commit()
        except Exception as inner_e:
            app.logger.error(f"Error al registrar el error de actividad: {str(inner_e)}")
        
        return False
    finally:
        # Asegurarse de cerrar la conexión y el cursor
        try:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
        except Exception as e:
            app.logger.error(f"Error al cerrar la conexión en log_user_activity: {str(e)}")

# Decorador para verificar permisos de administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Obtener el token del encabezado de autorización
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401
            
        try:
            # Decodificar el token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
            
            # Obtener el usuario actual
            current_user = get_user_by_id(current_user_id)
            if not current_user:
                return jsonify({'error': 'Usuario no encontrado'}), 404
                
            # Verificar si el usuario es administrador
            if current_user.get('rol_nombre') != 'admin':
                return jsonify({'error': 'Se requieren permisos de administrador'}), 403
                
            return f(current_user_id, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        except Exception as e:
            app.logger.error(f"Error en verificación de admin: {str(e)}")
            return jsonify({'error': 'Error en la autenticación'}), 500
            
    return decorated_function

# Rutas de la API para la gestión de usuarios
@app.route('/api/users', methods=['GET'])
@token_required
def get_users():
    """Obtiene la lista de usuarios."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        role_id = request.args.get('role_id', type=int)
        
        # Construir la consulta base
        tenant_id = get_current_tenant_id()
        
        query = """
            SELECT u.id, u.nombre, u.email, u.telefono, u.activo, u.fecha_creacion, 
                   r.nombre as rol_nombre
            FROM Users u
            LEFT JOIN Roles r ON u.rol_id = r.id
            WHERE u.activo = TRUE AND u.tenant_id = %s
        """
        
        params = [tenant_id]
        
        # Aplicar filtros
        if search:
            query += " AND (u.nombre LIKE %s OR u.email LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
            
        if role_id:
            query += " AND u.rol_id = %s"
            params.append(role_id)
        
        # Contar el total de resultados
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Aplicar paginación
        query += " ORDER BY u.fecha_creacion DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        # Ejecutar la consulta
        cursor.execute(query, params)
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'data': users,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        app.logger.error(f"Error al obtener usuarios: {str(e)}")
        return jsonify({'error': 'Error al obtener la lista de usuarios'}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    """Obtiene los detalles de un usuario específico."""
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
        
    # No devolver el hash de la contraseña
    user.pop('password', None)
    
    return jsonify(user)

def validate_password_strength(password):
    """
    Valida la fortaleza de una contraseña.
    
    Requisitos:
    - Mínimo 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un carácter especial
    
    Retorna:
    - (bool, str): Tupla con (es_valida, mensaje_error)
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una letra mayúscula"
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe contener al menos una letra minúscula"
    if not re.search(r"[0-9]", password):
        return False, "La contraseña debe contener al menos un número"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "La contraseña debe contener al menos un carácter especial"
    return True, ""

@app.route('/api/users', methods=['POST'])
@token_required
@admin_required
def create_user_route():
    """
    Crea un nuevo usuario en el sistema.
    
    Requiere autenticación y permisos de administrador.
    
    Parámetros (JSON):
    - nombre: Nombre completo del usuario (requerido)
    - email: Correo electrónico (requerido, debe ser único)
    - password: Contraseña (requerida, debe cumplir con los requisitos de seguridad)
    - telefono: Número de teléfono (opcional)
    - rol_id: ID del rol del usuario (opcional, por defecto 2 - usuario estándar)
    
    Retorna:
    - 201: Usuario creado correctamente
    - 400: Error en los datos de entrada
    - 403: No autorizado
    - 500: Error del servidor
    """
    try:
        # Verificar que el contenido sea JSON
        if not request.is_json:
            return jsonify({'error': 'El cuerpo de la solicitud debe ser JSON'}), 400
            
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['nombre', 'email', 'password']
        missing_fields = [field for field in required_fields if field not in data or not str(data[field]).strip()]
        
        if missing_fields:
            return jsonify({
                'error': 'Faltan campos requeridos',
                'missing_fields': missing_fields
            }), 400
        
        # Validar formato de email
        email = data['email'].strip()
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return jsonify({'error': 'El formato del correo electrónico no es válido'}), 400
        
        # Validar fortaleza de la contraseña
        password = data['password']
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            return jsonify({
                'error': 'La contraseña no cumple con los requisitos de seguridad',
                'details': error_message,
                'requirements': [
                    'Mínimo 8 caracteres',
                    'Al menos una letra mayúscula',
                    'Al menos una letra minúscula',
                    'Al menos un número',
                    'Al menos un carácter especial (!@#$%^&*(),.?:{}|<>)'
                ]
            }), 400
        
        # Verificar si el correo ya está en uso
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({
                'error': 'El correo electrónico ya está registrado',
                'suggestion': 'Utiliza otro correo electrónico o recupera tu contraseña si ya tienes una cuenta'
            }), 400
        cursor.close()
        conn.close()
        
        # Validar rol_id si se proporciona
        if 'rol_id' in data:
            try:
                role_id = int(data['rol_id'])
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM Roles WHERE id = %s", (role_id,))
                if not cursor.fetchone():
                    return jsonify({'error': 'El rol especificado no existe'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'El ID del rol debe ser un número entero'}), 400
            finally:
                cursor.close()
                conn.close()
        
        # Crear el usuario
        user_data = {
            'nombre': data['nombre'].strip(),
            'email': email,
            'password': password,
            'telefono': data.get('telefono', '').strip(),
            'rol_id': data.get('rol_id', 2)  # Por defecto, rol de usuario estándar
        }
        
        result = create_user(user_data)
        
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int) and result[1] >= 400:
            app.logger.error(f'Error al crear usuario: {result[0].get("error")}')
            return jsonify(result[0]), result[1]
        
        # Registrar actividad
        try:
            log_user_activity(g.user_id, 'user_created', {
                'created_user_id': result['id'],
                'email': result['email'],
                'rol_id': result.get('rol_id')
            })
        except Exception as e:
            app.logger.error(f'Error al registrar actividad de creación de usuario: {str(e)}')
        
        # No devolver el hash de la contraseña
        if 'password' in result:
            result.pop('password')
        
        return jsonify({
            'message': 'Usuario creado correctamente',
            'user': result
        }), 201
        
    except Exception as e:
        app.logger.error(f'Error en create_user_route: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Ocurrió un error al procesar la solicitud',
            'details': str(e) if app.debug else None
        }), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user_route(user_id):
    """
    Actualiza un usuario existente.
    
    Parámetros:
    - user_id: ID del usuario a actualizar
    
    Cuerpo de la solicitud (JSON):
    - nombre: Nombre del usuario (opcional)
    - email: Correo electrónico (opcional, debe ser único)
    - telefono: Número de teléfono (opcional)
    - password: Nueva contraseña (opcional)
    - rol_id: ID del rol (solo admin)
    - activo: Estado del usuario (solo admin)
    
    Retorna:
    - 200: Usuario actualizado correctamente
    - 400: Error en los datos de entrada
    - 403: No autorizado
    - 404: Usuario no encontrado
    - 500: Error interno del servidor
    """
    try:
        # Verificar datos de entrada
        if not request.is_json:
            return jsonify({'error': 'El cuerpo de la solicitud debe ser JSON'}), 400
            
        data = request.get_json()
        
        # Validar que el usuario exista
        target_user = get_user_by_id(user_id)
        if not target_user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Obtener el usuario actual
        current_user = get_user_by_id(g.user_id)
        if not current_user:
            return jsonify({'error': 'Usuario actual no encontrado'}), 404
            
        # Verificar permisos
        is_admin = current_user.get('rol_nombre') == 'admin'
        is_self = current_user['id'] == user_id
        
        if not is_self and not is_admin:
            app.logger.warning(f'Intento de actualización no autorizado. Usuario: {g.user_id} intentó actualizar usuario: {user_id}')
            return jsonify({'error': 'No tienes permiso para actualizar este usuario'}), 403
        
        # Validar formato de email si se está actualizando
        if 'email' in data:
            if not isinstance(data['email'], str) or not data['email'].strip():
                return jsonify({'error': 'El correo electrónico no puede estar vacío'}), 400
                
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', data['email']):
                return jsonify({'error': 'El formato del correo electrónico no es válido'}), 400
                
            # Verificar si el correo ya está en uso
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM Users WHERE email = %s AND id != %s", 
                         (data['email'], user_id))
            if cursor.fetchone():
                return jsonify({'error': 'El correo electrónico ya está en uso'}), 400
            cursor.close()
            conn.close()
        
        # Si el usuario no es admin, no permitir actualizar ciertos campos
        if not is_admin:
            restricted_fields = ['rol_id', 'activo']
            for field in restricted_fields:
                if field in data:
                    app.logger.warning(f'Intento de actualizar campo restringido: {field} por usuario no admin: {g.user_id}')
                    del data[field]
        
        # Validar rol_id si se está actualizando
        if 'rol_id' in data and is_admin:
            try:
                role_id = int(data['rol_id'])
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM Roles WHERE id = %s", (role_id,))
                if not cursor.fetchone():
                    return jsonify({'error': 'El rol especificado no existe'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'El ID del rol debe ser un número entero'}), 400
            finally:
                cursor.close()
                conn.close()
        
        # Actualizar el usuario
        result = update_user(user_id, data)
        
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int) and result[1] >= 400:
            app.logger.error(f'Error al actualizar usuario {user_id}: {result[0].get("error")}')
            return jsonify(result[0]), result[1]
        
        # Registrar actividad
        try:
            log_user_activity(g.user_id, 'user_updated', {
                'user_id': user_id,
                'updated_fields': list(data.keys()) if data else []
            })
        except Exception as e:
            app.logger.error(f'Error al registrar actividad de actualización de usuario: {str(e)}')
        
        # No devolver el hash de la contraseña
        if 'password' in result:
            result.pop('password')
        
        return jsonify({
            'message': 'Usuario actualizado correctamente',
            'user': result
        })
        
    except Exception as e:
        app.logger.error(f'Error en update_user_route: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Ocurrió un error al procesar la solicitud',
            'details': str(e) if app.debug else None
        }), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user_route(user_id):
    """Elimina un usuario (borrado lógico)."""
    # No permitir que un usuario se elimine a sí mismo
    if g.user_id == user_id:
        return jsonify({'error': 'No puedes eliminar tu propio usuario'}), 400
    
    result = delete_user(user_id)
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int) and result[1] >= 400:
        return jsonify(result[0]), result[1]
    
    # Registrar actividad
    log_user_activity(g.user_id, 'user_deleted', {'user_id': user_id})
    
    return jsonify(result)


@app.route('/api/users/me/password', methods=['PUT'])
@token_required
def change_my_password():
    """Permite a un usuario cambiar su propia contraseña."""
    data = request.get_json()
    
    # Validar datos requeridos
    required_fields = ['current_password', 'new_password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    # Obtener el usuario
    user = get_user_by_id(g.user_id)
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    # Verificar la contraseña actual
    if not bcrypt.checkpw(data['current_password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
        return jsonify({'error': 'La contraseña actual es incorrecta'}), 400
    
    # Actualizar la contraseña
    hashed_password = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt())
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE Users SET password = %s, fecha_actualizacion = NOW() WHERE id = %s",
            (hashed_password.decode('utf-8'), g.user_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Registrar actividad
        log_user_activity(g.user_id, 'password_changed')
        
        return jsonify({'message': 'Contraseña actualizada correctamente'})
    except Exception as e:
        app.logger.error(f"Error al actualizar contraseña: {str(e)}")
        return jsonify({'error': 'Error al actualizar la contraseña'}), 500

@app.route('/api/roles', methods=['GET'])
@token_required
def get_roles():
    """Obtiene la lista de roles disponibles."""
    try:
        roles = get_all_roles()
        return jsonify(roles)
    except Exception as e:
        app.logger.error(f"Error al obtener roles: {str(e)}")
        return jsonify({'error': 'Error al obtener la lista de roles'}), 500

# ===============================================================
# SECCIÓN 8: LÓGICA INTERNA DEL CHATBOT
# ===============================================================

def get_chatbot_settings():
    """Lee la configuración del chatbot desde la tabla Chatbot_Settings."""
    conn = get_db_connection()
    if not conn:
        return {"error": "No se pudo conectar a la BD para obtener la configuración."}
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT setting_name, setting_value FROM Chatbot_Settings")
        settings_from_db = {row['setting_name']: row['setting_value'] for row in cursor.fetchall()}
        
        return {
            "system_prompt": settings_from_db.get('system_prompt', 'ERROR: Prompt no configurado.'),
            "model": settings_from_db.get('chatbot_model', 'gpt-4o-mini'),
            "temperature": float(settings_from_db.get('chatbot_temperature', 0.7))
        }
    except Exception as e:
        app.logger.error(f"Error al leer la configuración del chatbot: {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()


# ===============================================================
# SECCIÓN 8: API DE HERRAMIENTAS PARA EL CHATBOT EXTERNO
# ===============================================================


# OLD BOT ENDPOINT REMOVED - Multi-tenant version available at /api/assistant/command
# @app.route('/api/bot_tools/vacancies', methods=['GET'])
# @require_api_key
# def bot_get_vacancies():
    """Endpoint seguro para que el bot de Node.js consulte vacantes."""
    city = request.args.get('city')
    keyword = request.args.get('keyword')
    app.logger.info("INICIANDO BÚSQUEDA DE VACANTES PARA BOT")
    app.logger.info(f"Parámetros recibidos: ciudad='{city}', palabra_clave='{keyword}'")
    
    conn = get_db_connection()
    if not conn: 
        app.logger.error("ERROR: Fallo en la conexión a la BD en bot_get_vacancies")
        return jsonify({"error": "DB connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT cargo_solicitado, ciudad FROM Vacantes WHERE estado = 'Abierta'"
        params = []
        
        if city:
            query += " AND LOWER(ciudad) LIKE LOWER(%s)"
            params.append(f"%{city}%")
        
        if keyword:
            query += " AND (LOWER(cargo_solicitado) LIKE LOWER(%s) OR LOWER(requisitos) LIKE LOWER(%s))"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        app.logger.info(f"Ejecutando SQL: {query}")
        app.logger.info(f"Con parámetros: {params}")
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        
        app.logger.info(f"SQL EJECUTADO. Número de resultados encontrados en la BD: {len(results)}")
        
        # Convertimos a JSON y lo registramos para auditoría
        response_json = json.dumps(results)
        app.logger.info(f"Respuesta JSON que se enviará a bridge.js (primeros 200 caracteres): {response_json[:200]}...")
        
        return Response(response_json, mimetype='application/json')
        
    except Exception as e:
        app.logger.error(f"ERROR crítico en bot_get_vacancies: {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/bot_tools/validate_registration', methods=['GET'])
@require_api_key
def bot_validate_registration():
    """
    Endpoint seguro para que el bot valide si un candidato con una identidad dada
    existe en el sistema.
    """
    identity_number = request.args.get('identity') or request.args.get('identity_number')
    
    app.logger.info(f"[Herramienta Validar] Parámetros recibidos en la URL: {request.args}")

    if not identity_number:
        return jsonify({"error": "Parámetro 'identity' es requerido."}), 400
        
    clean_identity = str(identity_number).replace('-', '').strip()

    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB connection failed"}), 500
    cursor = conn.cursor(dictionary=True)

    try:
        # La consulta ahora solo busca al afiliado. La existencia es el único criterio de éxito.
        query = "SELECT id_afiliado, nombre_completo FROM Afiliados WHERE identidad = %s LIMIT 1"
        cursor.execute(query, (clean_identity,))
        result = cursor.fetchone()

        if result:
            # --- LÓGICA CORREGIDA ---
            # Si se encuentra un resultado, SIEMPRE es un éxito.
            app.logger.info(f"Validación exitosa. Se encontró a {result['nombre_completo']} con identidad {clean_identity}")
            return jsonify({
                "success": True, 
                "candidate_name": result['nombre_completo'],
                "identity_verified": clean_identity # Devolvemos la identidad limpia para confirmación
            })
        else:
            # Si no se encuentra la identidad, es un fallo.
            app.logger.warning(f"Validación fallida. No se encontró candidato con identidad {clean_identity}")
            return jsonify({
                "success": False, 
                "message": "No hemos podido encontrar tu registro con esa identidad. Por favor, asegúrate de haber completado el formulario y de que el número sea correcto."
            })

    except Exception as e:
        app.logger.error(f"Error crítico en endpoint bot_validate_registration: {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
        

@app.route('/api/dashboard/activity_chart', methods=['GET'])
@token_required
def get_dashboard_activity():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Consulta para nuevos afiliados por día en los últimos 30 días
        sql_afiliados = """
            SELECT DATE(fecha_registro) as dia, COUNT(id_afiliado) as total 
            FROM Afiliados 
            WHERE fecha_registro >= CURDATE() - INTERVAL 30 DAY 
            GROUP BY DATE(fecha_registro) 
            ORDER BY dia;
        """
        cursor.execute(sql_afiliados)
        afiliados_data = cursor.fetchall()

        # Consulta para nuevas postulaciones por día en los últimos 30 días
        sql_postulaciones = """
            SELECT DATE(fecha_aplicacion) as dia, COUNT(id_postulacion) as total 
            FROM Postulaciones 
            WHERE fecha_aplicacion >= CURDATE() - INTERVAL 30 DAY 
            GROUP BY DATE(fecha_aplicacion) 
            ORDER BY dia;
        """
        cursor.execute(sql_postulaciones)
        postulaciones_data = cursor.fetchall()
        
        # Formatear fechas a string para JSON
        for row in afiliados_data: row['dia'] = row['dia'].isoformat()
        for row in postulaciones_data: row['dia'] = row['dia'].isoformat()

        return jsonify({
            "success": True, 
            "afiliados": afiliados_data, 
            "postulaciones": postulaciones_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
        

@app.route('/api/bot_tools/settings', methods=['GET'])
@require_api_key
def bot_get_settings():
    """
    Endpoint seguro para que el bot de Node.js obtenga su configuración
    (prompt, modelo, etc.) desde la base de datos del CRM.
    """
    try:
        settings = get_chatbot_settings() # Reutilizamos la función que ya creamos
        return jsonify(settings)
    except Exception as e:
        return jsonify({"error": str(e)}), 500  
    
    

@app.route('/api/bot_tools/all_active_vacancies', methods=['GET'])
@require_api_key
def bot_get_all_active_vacancies():
    """
    Endpoint seguro para que el bot obtenga una lista simple de TODOS 
    los cargos de las vacantes actualmente abiertas.
    """
    app.logger.info("[Herramienta Chatbot] Solicitando lista completa de vacantes activas")
    conn = get_db_connection()
    if not conn: 
        return jsonify({"error": "DB connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT cargo_solicitado FROM Vacantes WHERE estado = 'Abierta' ORDER BY cargo_solicitado ASC"
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Devolvemos una lista simple de strings para que sea ligera
        cargo_list = [row['cargo_solicitado'] for row in results]
        
        app.logger.info(f"Encontradas {len(cargo_list)} vacantes activas en total")
        return jsonify(cargo_list)
        
    except Exception as e:
        app.logger.error(f"Error en endpoint bot_get_all_active_vacancies: {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()     
        

@app.route('/api/bot_tools/vacancy_details', methods=['GET'])
@require_api_key
def bot_get_vacancy_details():
    """
    Endpoint seguro para que el bot obtenga los requisitos detallados
    de una vacante específica por su nombre.
    """
    cargo = request.args.get('cargo_solicitado')
    if not cargo:
        return jsonify({"error": "El 'cargo_solicitado' es requerido."}), 400

    app.logger.info(f"[Herramienta Chatbot] Buscando detalles para la vacante: '{cargo}'")
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Buscamos la vacante que más se parezca al cargo solicitado
        query = "SELECT cargo_solicitado, requisitos FROM Vacantes WHERE estado = 'Abierta' AND LOWER(cargo_solicitado) LIKE LOWER(%s) LIMIT 1"
        params = (f"%{cargo}%",)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        if result:
            app.logger.info(f"Encontrados detalles para '{result['cargo_solicitado']}'")
            return jsonify(result)
        else:
            app.logger.warning(f"No se encontraron detalles para la vacante '{cargo}'")
            return jsonify({"error": f"No se encontró una vacante llamada '{cargo}'."})
        
    except Exception as e:
        app.logger.error(f"Error en endpoint bot_get_vacancy_details: {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()        
        
        
# =================================================================
# INSERTAR NUEVA FUNCIÓN (Herramienta de Estado con Confidencialidad)
# =================================================================
@app.route('/api/bot_tools/candidate_status', methods=['GET'])
@require_api_key
def bot_get_candidate_status():
    """
    Endpoint seguro para que el bot consulte todas las postulaciones
    y su estado para un candidato específico, incluyendo detalles de entrevistas si existen.
    IMPORTANTE: Este endpoint NUNCA debe devolver el nombre de la empresa.
    """
    identity_number = request.args.get('identity_number')
    if not identity_number:
        return jsonify({"error": "El 'identity_number' es requerido."}), 400

    clean_identity = str(identity_number).replace('-', '').strip()
    app.logger.info(f"[Herramienta Chatbot] Buscando estado y entrevistas para identidad: '{clean_identity}'")
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Primero, encontramos al afiliado para asegurar que existe.
        cursor.execute("SELECT id_afiliado, nombre_completo FROM Afiliados WHERE identidad = %s", (clean_identity,))
        afiliado = cursor.fetchone()

        if not afiliado:
            app.logger.warning(f"No se encontró candidato con identidad {clean_identity}")
            return jsonify({"status": "not_registered"})

        # ✨ CONSULTA MEJORADA: Hacemos un LEFT JOIN con Entrevistas para obtener sus detalles
        query = """
            SELECT 
                p.id_postulacion,
                p.fecha_aplicacion,
                p.estado,
                v.cargo_solicitado,
                e.fecha_hora AS fecha_entrevista,
                e.entrevistador,
                e.observaciones AS detalles_entrevista
            FROM Postulaciones p
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            LEFT JOIN Entrevistas e ON p.id_postulacion = e.id_postulacion
            WHERE p.id_afiliado = %s
            ORDER BY p.fecha_aplicacion DESC;
        """
        cursor.execute(query, (afiliado['id_afiliado'],))
        postulaciones = cursor.fetchall()

        # Formateamos las fechas para que sean legibles y amigables
        for post in postulaciones:
            if post.get('fecha_aplicacion'):
                post['fecha_aplicacion'] = post['fecha_aplicacion'].strftime('%d de %B de %Y')
            if post.get('fecha_entrevista'):
                # Formato: Lunes, 01 de Agosto a las 03:30 PM
                post['fecha_entrevista'] = post['fecha_entrevista'].strftime('%A, %d de %B a las %I:%M %p')

        if not postulaciones:
            app.logger.info(f"Candidato '{afiliado['nombre_completo']}' encontrado, pero sin postulaciones")
            return jsonify({
                "status": "registered_no_applications", 
                "candidate_name": afiliado['nombre_completo']
            })
        
        app.logger.info(f"Encontradas {len(postulaciones)} postulaciones para '{afiliado['nombre_completo']}'")
        return jsonify({
            "status": "has_applications",
            "candidate_name": afiliado['nombre_completo'],
            "applications": postulaciones
        })
        
    except Exception as e:
        app.logger.error(f"Error en endpoint bot_get_candidate_status: {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Función para configurar tareas periódicas
def setup_periodic_tasks(sender, **kwargs):
    """Configura tareas periódicas para Celery"""
    # Recalcular puntuaciones de candidatos sin actividad reciente (ejecutar diariamente a las 2 AM)
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        recalculate_stale_scores.s(),
        name='recalcular-puntuaciones-diarias'
    )

# Tarea periódica para recalcular puntuaciones estancadas
# @celery_app.task(bind=True, name='recalculate_stale_scores')
def recalculate_stale_scores(self):
    """
    Tarea que recalcula puntuaciones de candidatos que no han sido actualizados
    en los últimos 7 días o que nunca han sido puntuados.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener candidatos que necesitan actualización
        cursor.execute("""
            SELECT id_afiliado 
            FROM Afiliados 
            WHERE ultima_actualizacion_puntuacion IS NULL 
               OR ultima_actualizacion_puntuacion < DATE_SUB(NOW(), INTERVAL 7 DAY)
            LIMIT 1000  # Limitar para no sobrecargar el sistema
        """)
        
        candidates = cursor.fetchall()
        total = len(candidates)
        logger.info(f"Iniciando recálculo de puntuaciones para {total} candidatos")
        
        # Procesar cada candidato
        for i, candidate in enumerate(candidates, 1):
            candidate_id = candidate['id_afiliado']
            try:
                # Actualizar estado de la tarea
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': total,
                        'status': f'Procesando candidato {i} de {total}'
                    }
                )
                
                # Ejecutar cálculo de puntuación
                calculate_candidate_score.delay(candidate_id)
                
            except Exception as e:
                logger.error(f"Error al programar cálculo para candidato {candidate_id}: {str(e)}")
        
        return {
            'total': total,
            'message': f'Se programó el recálculo para {total} candidatos'
        }
        
    except Exception as e:
        logger.error(f"Error en recalculate_stale_scores: {str(e)}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/bot_tools/vacancies_with_details', methods=['GET'])
@require_api_key
def bot_get_vacancies_with_details():
    """
    (NUEVA HERRAMIENTA) Endpoint para que el bot obtenga detalles completos 
    (cargo, ciudad, REQUISITOS) de TODAS las vacantes activas.
    Diseñada para ser usada solo cuando el bot necesite analizar los requisitos.
    """
    app.logger.info("[Herramienta Chatbot DETALLADA] Solicitando lista completa de vacantes con requisitos")
    conn = get_db_connection()
    if not conn: 
        return jsonify({"error": "DB connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT cargo_solicitado, ciudad, requisitos FROM Vacantes WHERE estado = 'Abierta'"
        cursor.execute(query)
        results = cursor.fetchall()
        app.logger.info(f"Encontradas {len(results)} vacantes con detalles para análisis")
        return jsonify(results)
        
    except Exception as e:
        app.logger.error(f"Error en endpoint bot_get_vacancies_with_details: {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/applications/update_notification_status', methods=['POST'])
@require_api_key
def update_notification_status():
    """Endpoint seguro para que bridge.js actualice el estado de una notificación."""
    data = request.get_json()
    postulation_id = data.get('postulation_id')
    status = data.get('status') # 'sent' o 'failed'

    if not all([postulation_id, status]):
        return jsonify({"error": "Faltan postulation_id o status"}), 400
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB connection failed"}), 500
    cursor = conn.cursor()
    try:
        sql = "UPDATE Postulaciones SET whatsapp_notification_status = %s WHERE id_postulacion = %s"
        cursor.execute(sql, (status, postulation_id))
        conn.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/applications/resync_pending_notifications', methods=['POST'])
@require_api_key
def resync_pending_notifications():
    """Busca todas las postulaciones con notificaciones pendientes y las re-envía a bridge.js."""
    app.logger.info("INICIANDO RESINCRONIZACIÓN DE NOTIFICACIONES PENDIENTES")
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    
    tasks_sent = 0
    try:
        # Solo buscamos postulaciones, las otras notificaciones son menos críticas si fallan.
        query = """
            SELECT p.id_postulacion, a.telefono, a.nombre_completo, v.cargo_solicitado, v.ciudad, v.salario, v.requisitos
            FROM Postulaciones p
            JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE p.whatsapp_notification_status = 'pending'
        """
        cursor.execute(query)
        pending_notifications = cursor.fetchall()

        for info in pending_notifications:
            salario_info = f"Salario: {info['salario']}" if info.get('salario') else "Salario: No especificado"
            message_body = (
                f"¡Hola {info['nombre_completo'].split(' ')[0]}! Te saluda Henmir. 👋\n\n"
                f"Hemos considerado tu perfil para una nueva oportunidad laboral y te hemos postulado a la siguiente vacante:\n\n"
                f"📌 *Puesto:* {info['cargo_solicitado']}\n"
                f"📍 *Ubicación:* {info['ciudad']}\n"
                f"💰 *{salario_info}*\n\n"
                f"*Requisitos principales:*\n{info['requisitos']}\n\n"
                "Por favor, confirma si estás interesado/a en continuar con este proceso. ¡Mucho éxito!"
            )
            task = {
                "task_type": "postulation",
                "related_id": info['id_postulacion'],
                "chat_id": clean_phone_number(info['telefono']),
                "message_body": message_body
            }
            if _send_task_to_bridge(task):
                tasks_sent += 1
        
        app.logger.info(f"Resincronización completada. {tasks_sent} tareas reenviadas a bridge.js.")
        return jsonify({"success": True, "tasks_resent": tasks_sent}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- FIN DEL NUEVO BLOQUE ---
# =================================================================

@app.route('/api/internal/all_affiliates_for_sync', methods=['GET'])
@require_api_key # Protegemos este endpoint para que solo nuestro bridge pueda usarlo
def get_all_affiliates_for_sync():
    """
    Endpoint interno y seguro diseñado para ser llamado únicamente por bridge.js.
    Devuelve una lista de todos los afiliados con un número de teléfono válido,
    junto con su número de identidad, para la sincronización inicial de estados.
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Seleccionamos solo los afiliados que tienen un número de teléfono, que es esencial para el chat.
        query = "SELECT identidad, telefono FROM Afiliados WHERE telefono IS NOT NULL AND telefono != ''"
        cursor.execute(query)
        affiliates = cursor.fetchall()
        
        # Limpiamos los números de teléfono para asegurar un formato consistente
        for affiliate in affiliates:
            affiliate['telefono'] = clean_phone_number(affiliate.get('telefono'))

        app.logger.info(f"Sincronización solicitada: Se encontraron {len(affiliates)} afiliados con teléfono para enviar a bridge.js.")
        return jsonify(affiliates)
        
    except Exception as e:
        app.logger.error(f"Error en el endpoint de sincronización de afiliados: {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/uploads/<path:folder>/<path:filename>')
def serve_uploaded_file(folder, filename):
    """
    Sirve los archivos guardados localmente desde el directorio /uploads.
    Esta es la ruta que permite que los enlaces a los CVs y fotos de ID funcionen.
    """
    # Medida de seguridad: solo permitir acceso a subcarpetas conocidas
    allowed_folders = ['cv', 'identidad', 'otros']
    if folder not in allowed_folders:
        return jsonify({"error": "Acceso no autorizado a esta carpeta."}), 403

    # Construye la ruta al directorio de uploads de forma segura
    # getcwd() obtiene el directorio de trabajo actual (donde corre app.py)
    upload_dir = os.path.join(os.getcwd(), 'uploads', folder)
    
    try:
        # La función de Flask 'send_from_directory' se encarga de servir el archivo de forma segura.
        # as_attachment=False intenta mostrar el archivo en el navegador (ej. un PDF) en lugar de descargarlo.
        return send_from_directory(upload_dir, filename, as_attachment=False)
    except FileNotFoundError:
        return jsonify({"error": "Archivo no encontrado."}), 404


@app.route('/api/internal/chat_context/<string:identity_number>', methods=['GET'])
@require_api_key
def get_chat_context_by_identity(identity_number):
    """
    Endpoint interno para que bridge.js obtenga el contexto completo de un
    afiliado para mostrarlo en el panel de chat.
    Devuelve información básica y sus últimas 3 postulaciones.
    """
    clean_identity = str(identity_number).replace('-', '').strip()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        context_data = {
            "info_basica": None,
            "ultimas_postulaciones": []
        }

        # 1. Obtener información básica del afiliado
        cursor.execute("SELECT id_afiliado, nombre_completo, identidad, telefono, ciudad FROM Afiliados WHERE identidad = %s", (clean_identity,))
        info_basica = cursor.fetchone()

        if not info_basica:
            return jsonify({"error": "Afiliado no encontrado"}), 404
            
        context_data["info_basica"] = info_basica
        id_afiliado = info_basica['id_afiliado']

        # 2. Obtener las últimas 3 postulaciones del afiliado
        postulaciones_query = """
            SELECT p.id_postulacion, p.fecha_aplicacion, p.estado, v.cargo_solicitado, c.empresa
            FROM Postulaciones p
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            JOIN Clientes c ON v.id_cliente = c.id_cliente
            WHERE p.id_afiliado = %s
            ORDER BY p.fecha_aplicacion DESC
            LIMIT 3
        """
        cursor.execute(postulaciones_query, (id_afiliado,))
        postulaciones = cursor.fetchall()

        # Formatear fechas para que sean compatibles con JSON
        for p in postulaciones:
            if isinstance(p.get('fecha_aplicacion'), (datetime, date)):
                p['fecha_aplicacion'] = p['fecha_aplicacion'].isoformat()

        context_data["ultimas_postulaciones"] = postulaciones

        return jsonify(context_data)
        
    except Exception as e:
        app.logger.error(f"Error en el endpoint de contexto de chat: {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
        

# --- INICIO DE CÓDIGO A AÑADIR ---
def create_initial_user():
    """
    Verifica si existe un usuario inicial y, si no, lo crea.
    Ideal para la primera ejecución del sistema.
    """
    conn = get_db_connection()
    if not conn:
        app.logger.error("ERROR: No se pudo conectar a la BD para crear el usuario inicial.")
        return
    
    cursor = conn.cursor()
    
    try:
        # --- CONFIGURA TUS CREDENCIALES INICIALES AQUÍ ---
        initial_email = "agencia.henmir@gmail.com"
        initial_password = "Nc044700" # ¡CÁMBIALA!

        # Revisa si el usuario ya existe
        cursor.execute("SELECT id FROM Users WHERE email = %s", (initial_email,))
        if cursor.fetchone():
            app.logger.info(f"INFO: El usuario '{initial_email}' ya existe.")
            return

        # Si no existe, lo crea
        app.logger.info(f"INFO: Creando usuario inicial '{initial_email}'...")
        hashed_password = bcrypt.hashpw(initial_password.encode('utf-8'), bcrypt.gensalt())
        
        query = "INSERT INTO Users (email, password_hash) VALUES (%s, %s)"
        cursor.execute(query, (initial_email, hashed_password.decode('utf-8')))
        conn.commit()
        app.logger.info(f"ÉXITO: Usuario '{initial_email}' creado. ¡Recuerda esta contraseña!")

    except Exception as e:
        app.logger.error(f"ERROR: No se pudo crear el usuario inicial. {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        cursor.close()
        conn.close()

@app.route('/api/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats():
    """Obtiene estadísticas generales del dashboard."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener tenant_id del usuario actual
        tenant_id = get_current_tenant_id()
        
        # Estadísticas de candidatos
        cursor.execute("""
            SELECT 
                COUNT(*) as total_candidatos,
                COUNT(CASE WHEN estado = 'active' THEN 1 END) as candidatos_activos,
                COUNT(CASE WHEN DATE(fecha_registro) = CURDATE() THEN 1 END) as candidatos_hoy
            FROM Afiliados a
            WHERE %s IS NULL OR a.id_afiliado IN (
                SELECT DISTINCT p.id_afiliado 
                FROM Postulaciones p 
                JOIN Vacantes v ON p.id_vacante = v.id_vacante 
                WHERE v.id_cliente = %s
            )
        """, (tenant_id, tenant_id) if tenant_id else (None, None))
        
        candidatos_stats = cursor.fetchone()
        
        # Estadísticas de aplicaciones
        cursor.execute("""
            SELECT 
                COUNT(*) as total_aplicaciones,
                COUNT(CASE WHEN p.estado = 'Contratado' THEN 1 END) as contratados,
                COUNT(CASE WHEN p.estado = 'Entrevista' THEN 1 END) as entrevistas,
                COUNT(CASE WHEN DATE(p.fecha_aplicacion) = CURDATE() THEN 1 END) as aplicaciones_hoy
            FROM Postulaciones p
            JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE %s IS NULL OR v.id_cliente = %s
        """, (tenant_id, tenant_id) if tenant_id else (None, None))
        
        aplicaciones_stats = cursor.fetchone()
        
        # Estadísticas de vacantes
        cursor.execute("""
            SELECT
                COUNT(*) as total_vacantes,
                COUNT(CASE WHEN estado = 'Abierta' THEN 1 END) as vacantes_abiertas,
                COUNT(CASE WHEN DATE(fecha_apertura) = CURDATE() THEN 1 END) as vacantes_hoy
            FROM Vacantes v
            WHERE %s IS NULL OR v.id_cliente = %s
        """, (tenant_id, tenant_id) if tenant_id else (None, None))
        
        vacantes_stats = cursor.fetchone()
        
        # Calcular tasa de conversión
        total_aplicaciones = aplicaciones_stats['total_aplicaciones'] or 0
        contratados = aplicaciones_stats['contratados'] or 0
        tasa_conversion = (contratados / total_aplicaciones * 100) if total_aplicaciones > 0 else 0
        
        # Calcular tiempo promedio de respuesta (simulado por ahora)
        tiempo_respuesta = "1.5min"  # Esto se puede calcular con datos reales más adelante
        
        # Calcular cambios porcentuales (simulados por ahora - se pueden calcular con datos históricos)
        cambio_candidatos = "+12%"  # Se puede calcular comparando con el mes anterior
        cambio_conversion = "+5%" if tasa_conversion > 0 else "0%"
        cambio_automatizacion = "+8%"  # Porcentaje de procesos automatizados
        cambio_respuesta = "-15%"  # Mejora en tiempo de respuesta
        
        stats = {
            'candidatos_activos': {
                'valor': candidatos_stats['candidatos_activos'] or 0,
                'cambio': cambio_candidatos,
                'label': 'Candidatos Activos'
            },
            'tasa_conversion': {
                'valor': f"{tasa_conversion:.1f}%",
                'cambio': cambio_conversion,
                'label': 'Tasa de Conversión'
            },
            'automatizacion': {
                'valor': "94%",  # Porcentaje de procesos automatizados
                'cambio': cambio_automatizacion,
                'label': 'IA Automatizada'
            },
            'tiempo_respuesta': {
                'valor': tiempo_respuesta,
                'cambio': cambio_respuesta,
                'label': 'Tiempo de Respuesta'
            }
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        app.logger.error(f"Error obteniendo estadísticas del dashboard: {e}")
        return jsonify({
            'success': False,
            'error': 'Error al obtener estadísticas del dashboard'
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Los endpoints de WhatsApp se manejan en bridge.js (Node.js)
# Aquí solo registramos la comunicación entre sistemas

# --- ACCIÓN: Llama a la función aquí ---
create_initial_user()

# ==================== ENDPOINTS DEL CALENDARIO ====================

@app.route('/api/calendar/reminders', methods=['GET', 'POST'])
@token_required
def calendar_reminders():
    """Gestionar recordatorios del calendario"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        tenant_id = get_current_tenant_id() or 1  # Fallback a tenant 1 para pruebas
        
        if request.method == 'GET':
            # Obtener recordatorios
            year = request.args.get('year', datetime.now().year)
            month = request.args.get('month', datetime.now().month)
            
            cursor.execute("""
                SELECT r.*, u.username as created_by_name
                FROM calendar_reminders r
                LEFT JOIN Users u ON r.created_by = u.id
                WHERE r.tenant_id = %s 
                AND YEAR(r.date) = %s 
                AND MONTH(r.date) = %s
                ORDER BY r.date, r.time
            """, (tenant_id, year, month))
            
            reminders = cursor.fetchall()
            
            # Convertir timedelta objects a strings para JSON serialization
            for reminder in reminders:
                if reminder.get('time') and hasattr(reminder['time'], 'total_seconds'):
                    # Convertir timedelta a string HH:MM:SS
                    total_seconds = int(reminder['time'].total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    reminder['time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            return jsonify({'success': True, 'data': reminders})
            
        elif request.method == 'POST':
            # Crear nuevo recordatorio
            data = request.json
            user_id = g.current_user['id']
            
            cursor.execute("""
                INSERT INTO calendar_reminders 
                (tenant_id, title, description, date, time, type, priority, status, created_by, assigned_to)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tenant_id,
                data['title'],
                data.get('description', ''),
                data['date'],
                data['time'],
                data['type'],
                data.get('priority', 'medium'),
                'pending',
                user_id,
                json.dumps(data.get('assigned_to', []))
            ))
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Recordatorio creado exitosamente'})
            
    except Exception as e:
        app.logger.error(f"Error en calendar_reminders: {str(e)}")
        return jsonify({'error': 'Error al gestionar recordatorios'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/calendar/interviews', methods=['GET'])
@token_required
def calendar_interviews():
    """Obtener entrevistas del calendario"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        tenant_id = get_current_tenant_id() or 1  # Fallback a tenant 1 para pruebas
        
        year = request.args.get('year', datetime.now().year)
        month = request.args.get('month', datetime.now().month)
        
        cursor.execute("""
            SELECT 
                i.id,
                i.candidate_id,
                a.nombre_completo as candidate_name,
                i.vacancy_id,
                v.cargo_solicitado as vacancy_title,
                i.interview_date as date,
                i.interview_time as time,
                i.status,
                i.notes,
                i.interviewer,
                i.created_at
            FROM interviews i
            LEFT JOIN Afiliados a ON i.candidate_id = a.id_afiliado
            LEFT JOIN Vacantes v ON i.vacancy_id = v.id_vacante
            WHERE i.tenant_id = %s 
            AND YEAR(i.interview_date) = %s 
            AND MONTH(i.interview_date) = %s
            ORDER BY i.interview_date, i.interview_time
        """, (tenant_id, year, month))
        
        interviews = cursor.fetchall()
        
        # Convertir timedelta objects a strings para JSON serialization
        for interview in interviews:
            if interview.get('time') and hasattr(interview['time'], 'total_seconds'):
                # Convertir timedelta a string HH:MM:SS
                total_seconds = int(interview['time'].total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                interview['time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        return jsonify({'success': True, 'data': interviews})
        
    except Exception as e:
        app.logger.error(f"Error en calendar_interviews: {str(e)}")
        return jsonify({'error': 'Error al obtener entrevistas'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/calendar/activities', methods=['GET'])
@token_required
def calendar_activities():
    """Obtener actividades del calendario"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        tenant_id = get_current_tenant_id() or 1  # Fallback a tenant 1 para pruebas
        
        year = request.args.get('year', datetime.now().year)
        month = request.args.get('month', datetime.now().month)
        
        # Actividades de postulaciones
        cursor.execute("""
            SELECT 
                CONCAT('postulation_', p.id_postulacion) as id,
                'application' as type,
                CONCAT('Nueva postulación: ', a.nombre_completo) as description,
                a.nombre_completo as candidate_name,
                v.cargo_solicitado as vacancy_title,
                p.fecha_aplicacion as timestamp,
                NULL as user_id,
                'Sistema' as user_name
            FROM Postulaciones p
            LEFT JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
            LEFT JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE YEAR(p.fecha_aplicacion) = %s 
            AND MONTH(p.fecha_aplicacion) = %s
            
            UNION ALL
            
            SELECT 
                CONCAT('interview_', i.id) as id,
                'interview' as type,
                CONCAT('Entrevista programada: ', a.nombre_completo) as description,
                a.nombre_completo as candidate_name,
                v.cargo_solicitado as vacancy_title,
                i.created_at as timestamp,
                i.created_by as user_id,
                u.username as user_name
            FROM interviews i
            LEFT JOIN Afiliados a ON i.candidate_id = a.id_afiliado
            LEFT JOIN Vacantes v ON i.vacancy_id = v.id_vacante
            LEFT JOIN Users u ON i.created_by = u.id
            WHERE i.tenant_id = %s 
            AND YEAR(i.created_at) = %s 
            AND MONTH(i.created_at) = %s
            
            ORDER BY timestamp DESC
        """, (year, month, tenant_id, year, month))
        
        activities = cursor.fetchall()
        
        # Convertir datetime objects a strings para JSON serialization
        for activity in activities:
            if activity.get('timestamp') and hasattr(activity['timestamp'], 'isoformat'):
                activity['timestamp'] = activity['timestamp'].isoformat()
        
        return jsonify({'success': True, 'data': activities})
        
    except Exception as e:
        app.logger.error(f"Error en calendar_activities: {str(e)}")
        return jsonify({'error': 'Error al obtener actividades'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/calendar/reminders/<int:reminder_id>', methods=['PUT', 'DELETE'])
@token_required
def calendar_reminder_detail(reminder_id):
    """Actualizar o eliminar recordatorio específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        tenant_id = get_current_tenant_id() or 1  # Fallback a tenant 1 para pruebas
        user_id = g.current_user['id']
        
        # Verificar que el recordatorio existe y pertenece al tenant
        cursor.execute("""
            SELECT * FROM calendar_reminders 
            WHERE id = %s AND tenant_id = %s
        """, (reminder_id, tenant_id))
        
        reminder = cursor.fetchone()
        if not reminder:
            return jsonify({'error': 'Recordatorio no encontrado'}), 404
        
        # Verificar permisos (solo el creador puede modificar/eliminar)
        if reminder['created_by'] != user_id and g.current_user['role'] not in ['admin', 'supervisor']:
            return jsonify({'error': 'No tienes permisos para modificar este recordatorio'}), 403
        
        if request.method == 'PUT':
            # Actualizar recordatorio
            data = request.json
            
            cursor.execute("""
                UPDATE calendar_reminders 
                SET title = %s, description = %s, date = %s, time = %s, 
                    type = %s, priority = %s, status = %s, assigned_to = %s
                WHERE id = %s AND tenant_id = %s
            """, (
                data['title'],
                data.get('description', ''),
                data['date'],
                data['time'],
                data['type'],
                data.get('priority', 'medium'),
                data.get('status', 'pending'),
                json.dumps(data.get('assigned_to', [])),
                reminder_id,
                tenant_id
            ))
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Recordatorio actualizado exitosamente'})
            
        elif request.method == 'DELETE':
            # Eliminar recordatorio
            cursor.execute("""
                DELETE FROM calendar_reminders 
                WHERE id = %s AND tenant_id = %s
            """, (reminder_id, tenant_id))
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Recordatorio eliminado exitosamente'})

    except Exception as e:
        app.logger.error(f"Error en calendar_reminder_detail: {str(e)}")
        return jsonify({'error': 'Error al gestionar recordatorio'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ==================== ENDPOINTS DE CLIENTES DETALLADOS ====================

@app.route('/api/clients/<int:client_id>/vacancies', methods=['GET'])
@token_required
def get_client_vacancies(client_id):
    """Obtener vacantes de un cliente específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        tenant_id = get_current_tenant_id()
        
        cursor.execute("""
            SELECT 
                v.id_vacante,
                v.cargo_solicitado,
                v.ciudad,
                v.requisitos,
                v.salario,
                v.fecha_apertura,
                v.fecha_cierre,
                v.estado,
                v.created_at
            FROM Vacantes v
            WHERE v.id_cliente = %s
            ORDER BY v.fecha_apertura DESC
        """, (client_id,))
        
        vacancies = cursor.fetchall()
        
        # Convertir datetime objects a strings para JSON serialization
        for vacancy in vacancies:
            if vacancy.get('fecha_apertura') and hasattr(vacancy['fecha_apertura'], 'isoformat'):
                vacancy['fecha_apertura'] = vacancy['fecha_apertura'].isoformat()
            if vacancy.get('fecha_cierre') and hasattr(vacancy['fecha_cierre'], 'isoformat'):
                vacancy['fecha_cierre'] = vacancy['fecha_cierre'].isoformat()
            if vacancy.get('created_at') and hasattr(vacancy['created_at'], 'isoformat'):
                vacancy['created_at'] = vacancy['created_at'].isoformat()
        
        return jsonify({'success': True, 'data': vacancies})
        
    except Exception as e:
        app.logger.error(f"Error en get_client_vacancies: {str(e)}")
        return jsonify({'error': 'Error al obtener vacantes del cliente'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/clients/<int:client_id>/applications', methods=['GET'])
@token_required
def get_client_applications(client_id):
    """Obtener postulaciones de un cliente específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        tenant_id = get_current_tenant_id()
        
        cursor.execute("""
            SELECT
                p.id_postulacion,
                p.id_afiliado,
                a.nombre_completo,
                a.email,
                a.telefono,
                p.fecha_aplicacion,
                p.estado,
                v.cargo_solicitado,
                p.id_vacante,
                p.comentarios as notas
            FROM Postulaciones p
            LEFT JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
            LEFT JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE v.id_cliente = %s
            ORDER BY p.fecha_aplicacion DESC
        """, (client_id,))
        
        applications = cursor.fetchall()
        
        # Convertir datetime objects a strings para JSON serialization
        for application in applications:
            if application.get('fecha_aplicacion') and hasattr(application['fecha_aplicacion'], 'isoformat'):
                application['fecha_aplicacion'] = application['fecha_aplicacion'].isoformat()
        
        return jsonify({'success': True, 'data': applications})
        
    except Exception as e:
        app.logger.error(f"Error en get_client_applications: {str(e)}")
        return jsonify({'error': 'Error al obtener postulaciones del cliente'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/clients/<int:client_id>/hired-candidates', methods=['GET'])
@token_required
def get_client_hired_candidates(client_id):
    """Obtener candidatos contratados de un cliente específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        tenant_id = get_current_tenant_id()
        
        cursor.execute("""
            SELECT 
                a.id_afiliado,
                a.nombre_completo,
                a.email,
                v.cargo_solicitado as cargo_contratado,
                p.fecha_aplicacion as fecha_contratacion,
                v.salario as salario,
                p.id_vacante as vacante_id
            FROM Postulaciones p
            LEFT JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
            LEFT JOIN Vacantes v ON p.id_vacante = v.id_vacante
            WHERE v.id_cliente = %s 
            AND p.estado = 'Aprobado'
            ORDER BY p.fecha_aplicacion DESC
        """, (client_id,))
        
        hired_candidates = cursor.fetchall()
        
        # Convertir datetime objects a strings para JSON serialization
        for candidate in hired_candidates:
            if candidate.get('fecha_contratacion') and hasattr(candidate['fecha_contratacion'], 'isoformat'):
                candidate['fecha_contratacion'] = candidate['fecha_contratacion'].isoformat()
        
        return jsonify({'success': True, 'data': hired_candidates})
        
    except Exception as e:
        app.logger.error(f"Error en get_client_hired_candidates: {str(e)}")
        return jsonify({'error': 'Error al obtener candidatos contratados'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ENDPOINT DUPLICADO - COMENTADO PARA EVITAR CONFLICTOS
# Usar /api/applications/<int:id_postulacion>/status en su lugar
# @app.route('/api/applications/<int:application_id>/status', methods=['PUT'])
# @token_required
# def update_application_status_from_client(application_id):
#     """Actualizar estado de una postulación"""
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         tenant_id = get_current_tenant_id()
#         user_id = g.current_user['id']
#         
#         data = request.json
#         new_status = data.get('status')
#         
#         if not new_status:
#             return jsonify({'error': 'Estado requerido'}), 400
#         
#         # Verificar que la postulación existe
#         cursor.execute("""
#             SELECT p.*, v.id_cliente
#             FROM Postulaciones p
#             LEFT JOIN Vacantes v ON p.id_vacante = v.id_vacante
#             WHERE p.id_postulacion = %s
#         """, (application_id,))
#         
#         application = cursor.fetchone()
#         if not application:
#             return jsonify({'error': 'Postulación no encontrada'}), 404
#         
#         # Actualizar estado
#         cursor.execute("""
#             UPDATE Postulaciones 
#             SET estado = %s, created_at = CURRENT_TIMESTAMP
#             WHERE id_postulacion = %s
#         """, (new_status, application_id))
#         
#         conn.commit()
#         return jsonify({'success': True, 'message': 'Estado actualizado exitosamente'})
#         
#     except Exception as e:
#         app.logger.error(f"Error en update_application_status: {str(e)}")
#         return jsonify({'error': 'Error al actualizar estado'}), 500
#     finally:
#         if 'cursor' in locals():
#             cursor.close()
#         if 'conn' in locals():
#             conn.close()

# ==================== ENDPOINTS DE PERMISOS ====================

@app.route('/api/permissions', methods=['GET'])
@token_required
def get_permissions():
    """Obtener permisos del usuario actual"""
    try:
        user = g.current_user
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        # Obtener rol del usuario
        rol = user.get('rol', '')
        
        # Definir permisos basados en el rol
        permissions = {
            "all": rol == 'Administrador',
            "candidates": True,  # Todos pueden ver candidatos
            "applications": True,  # Todos pueden ver aplicaciones
            "clients": rol in ['Administrador', 'Reclutador'],
            "users": rol == 'Administrador',
            "reports": rol in ['Administrador', 'Reclutador'],
            "settings": rol == 'Administrador'
        }
        
        return jsonify({
            "success": True,
            "permissions": permissions,
            "user": {
                "id": user.get('id'),
                "email": user.get('email'),
                "rol": rol
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error en get_permissions: {str(e)}")
        return jsonify({"error": "Error al obtener permisos"}), 500

# ==================== ENDPOINTS DE CARGA MASIVA DE CVs ====================

@app.route('/api/candidates/upload', methods=['POST'])
@token_required
def upload_cvs():
    """Cargar CVs individual o masivamente"""
    try:
        app.logger.info(f"Upload CVs - User ID: {g.current_user.get('id')}, Tenant ID: {get_current_tenant_id()}")
        app.logger.info(f"g.current_user completo: {g.current_user}")
        tenant_id = get_current_tenant_id()
        user_id = g.current_user.get('id') or g.current_user.get('user_id')
        
        if not user_id:
            app.logger.error("No se pudo obtener user_id del token")
            app.logger.error(f"g.current_user keys: {list(g.current_user.keys()) if g.current_user else 'None'}")
            return jsonify({'error': 'Error de autenticación: ID de usuario no encontrado'}), 401
        
        # Verificar si hay archivos
        if 'files' not in request.files:
            return jsonify({'error': 'No se encontraron archivos'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No se seleccionaron archivos válidos'}), 400
        
        # Validar tipos de archivo
        allowed_extensions = {'.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        valid_files = []
        
        for file in files:
            if file.filename:
                file_ext = os.path.splitext(file.filename.lower())[1]
                if file_ext in allowed_extensions:
                    valid_files.append(file)
                else:
                    return jsonify({'error': f'Tipo de archivo no soportado: {file_ext}'}), 400
        
        if not valid_files:
            return jsonify({'error': 'No hay archivos válidos para procesar'}), 400
        
        # Crear gestor de lotes
        try:
            from cv_batch_manager import create_batch_manager
            batch_manager = create_batch_manager()
            app.logger.info("Batch manager creado exitosamente")
        except Exception as e:
            app.logger.error(f"Error importando batch manager: {e}")
            return jsonify({'error': 'Error inicializando procesador de CVs'}), 500
        
        # Preparar archivos para procesamiento
        try:
            files_data = []
            for i, file in enumerate(valid_files):
                # Guardar archivo temporalmente
                filename = secure_filename(file.filename)
                file_path = os.path.join('temp_uploads', f"{tenant_id}_{user_id}_{i}_{filename}")
                os.makedirs('temp_uploads', exist_ok=True)
                file.save(file_path)
                
                files_data.append({
                    'file_path': file_path,
                    'original_name': file.filename,
                    'file_type': os.path.splitext(filename)[1][1:].lower()
                })
            
            app.logger.info(f"Archivos preparados: {len(files_data)}")
        except Exception as e:
            app.logger.error(f"Error preparando archivos: {e}")
            return jsonify({'error': 'Error preparando archivos'}), 500
        
        # Crear trabajo de procesamiento
        try:
            job_id = batch_manager.create_job(files_data, tenant_id, user_id)
            app.logger.info(f"Trabajo creado: {job_id}")
        except Exception as e:
            app.logger.error(f"Error creando trabajo: {e}")
            return jsonify({'error': 'Error creando trabajo de procesamiento'}), 500
        
        # Iniciar procesamiento en background
        try:
            import threading
            def process_background():
                try:
                    app.logger.info(f"Iniciando procesamiento del trabajo {job_id}")
                    batch_manager.process_job(job_id)
                    app.logger.info(f"Procesamiento completado para trabajo {job_id}")
                except Exception as e:
                    app.logger.error(f"Error procesando trabajo {job_id}: {e}")
            
            thread = threading.Thread(target=process_background)
            thread.daemon = True
            thread.start()
            app.logger.info(f"Thread de procesamiento iniciado para trabajo {job_id}")
        except Exception as e:
            app.logger.error(f"Error iniciando procesamiento en background: {e}")
            return jsonify({'error': 'Error iniciando procesamiento'}), 500
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'total_files': len(valid_files),
            'message': 'Procesamiento iniciado'
        })
        
    except Exception as e:
        app.logger.error(f"Error en upload_cvs: {str(e)}")
        return jsonify({'error': 'Error al procesar archivos'}), 500

@app.route('/api/candidates/process-status/<job_id>', methods=['GET'])
@token_required
def get_processing_status(job_id):
    """Obtener estado del procesamiento"""
    try:
        tenant_id = get_current_tenant_id()
        
        from cv_batch_manager import create_batch_manager
        batch_manager = create_batch_manager()
        
        job_data = batch_manager.get_job_status(job_id)
        
        # Verificar que el trabajo pertenece al tenant
        if job_data.get('tenant_id') != tenant_id:
            return jsonify({'error': 'Trabajo no encontrado'}), 404
        
        return jsonify({
            'success': True,
            'job_data': job_data
        })
        
    except FileNotFoundError:
        return jsonify({'error': 'Trabajo no encontrado'}), 404
    except Exception as e:
        app.logger.error(f"Error en get_processing_status: {str(e)}")
        return jsonify({'error': 'Error al obtener estado'}), 500

@app.route('/api/candidates/check-duplicates', methods=['POST'])
@token_required
def check_duplicates():
    """Verificar duplicados antes del procesamiento usando múltiples criterios"""
    try:
        tenant_id = get_current_tenant_id()
        data = request.json
        
        if not data or 'candidates' not in data:
            return jsonify({'error': 'Lista de candidatos requerida'}), 400
        
        candidates = data['candidates']
        if not isinstance(candidates, list):
            return jsonify({'error': 'Candidatos debe ser una lista'}), 400
        
        # Importar detector de duplicados
        from cv_duplicate_detector import create_duplicate_detector
        duplicate_detector = create_duplicate_detector()
        
        duplicates_found = []
        
        for candidate in candidates:
            # Buscar duplicados usando múltiples criterios
            duplicates = duplicate_detector.find_duplicates_comprehensive(candidate, tenant_id)
            
            if duplicates:
                # Calcular confianza para cada duplicado
                for duplicate in duplicates:
                    confidence = duplicate_detector.calculate_duplicate_confidence(candidate, duplicate)
                    duplicate_type = duplicate_detector.classify_duplicate(candidate, duplicate)
                    
                    duplicates_found.append({
                        'candidate': candidate,
                        'duplicate': duplicate,
                        'confidence': confidence,
                        'type': duplicate_type
                    })
        
        return jsonify({
            'success': True,
            'duplicates': duplicates_found,
            'total_checked': len(candidates),
            'duplicates_found': len(duplicates_found)
        })

    except Exception as e:
        app.logger.error(f"Error en check_duplicates: {str(e)}")
        return jsonify({'error': 'Error al verificar duplicados'}), 500

@app.route('/api/candidates/batch-results/<job_id>', methods=['GET'])
@token_required
def get_batch_results(job_id):
    """Obtener resultados detallados del procesamiento"""
    try:
        tenant_id = get_current_tenant_id()
        
        from cv_batch_manager import create_batch_manager
        batch_manager = create_batch_manager()
        
        job_data = batch_manager.get_job_status(job_id)
        
        # Verificar que el trabajo pertenece al tenant
        if job_data.get('tenant_id') != tenant_id:
            return jsonify({'error': 'Trabajo no encontrado'}), 404
        
        return jsonify({
            'success': True,
            'results': job_data.get('results', []),
            'summary': {
                'total_files': job_data.get('total_files', 0),
                'processed': job_data.get('processed_files', 0),
                'successful': job_data.get('successful', 0),
                'errors': job_data.get('errors', 0),
                'duplicates': job_data.get('duplicates', 0)
            },
            'status': job_data.get('status', 'unknown')
        })
        
    except FileNotFoundError:
        return jsonify({'error': 'Trabajo no encontrado'}), 404
    except Exception as e:
        app.logger.error(f"Error en get_batch_results: {str(e)}")
        return jsonify({'error': 'Error al obtener resultados'}), 500

@app.route('/api/candidates/cancel-job/<job_id>', methods=['POST'])
@token_required
def cancel_job(job_id):
    """Cancelar un trabajo de procesamiento"""
    try:
        tenant_id = get_current_tenant_id()
        
        from cv_batch_manager import create_batch_manager
        batch_manager = create_batch_manager()
        
        result = batch_manager.cancel_job(job_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
        
    except Exception as e:
        app.logger.error(f"Error cancelando trabajo {job_id}: {str(e)}")
        return jsonify({'error': 'Error cancelando trabajo'}), 500

@app.route('/api/candidates/<int:candidate_id>/missing-fields', methods=['GET'])
@token_required
def get_candidate_missing_fields(candidate_id):
    """Obtener campos faltantes de un candidato"""
    try:
        tenant_id = get_current_tenant_id()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener candidato
        cursor.execute("""
            SELECT * FROM Afiliados 
            WHERE id_afiliado = %s AND tenant_id = %s
        """, (candidate_id, tenant_id))
        
        candidate = cursor.fetchone()
        if not candidate:
            return jsonify({'error': 'Candidato no encontrado'}), 404
        
        # Analizar campos faltantes
        missing_fields = []
        warnings = []
        
        # Campos críticos
        if not candidate.get('email') or candidate.get('email', '').endswith('@temp.com'):
            missing_fields.append({
                'field': 'email',
                'label': 'Correo Electrónico',
                'required': True,
                'current_value': candidate.get('email'),
                'is_temporary': candidate.get('email', '').endswith('@temp.com')
            })
        
        if not candidate.get('telefono'):
            missing_fields.append({
                'field': 'telefono',
                'label': 'Teléfono',
                'required': False,
                'current_value': candidate.get('telefono')
            })
        
        if not candidate.get('ciudad'):
            missing_fields.append({
                'field': 'ciudad',
                'label': 'Ciudad',
                'required': False,
                'current_value': candidate.get('ciudad')
            })
        
        if not candidate.get('cargo_solicitado'):
            missing_fields.append({
                'field': 'cargo_solicitado',
                'label': 'Cargo Solicitado',
                'required': False,
                'current_value': candidate.get('cargo_solicitado')
            })
        
        # Analizar habilidades
        habilidades_json = candidate.get('habilidades')
        if not habilidades_json or habilidades_json == '[]' or habilidades_json == 'null':
            missing_fields.append({
                'field': 'habilidades',
                'label': 'Habilidades',
                'required': False,
                'current_value': 'No especificadas',
                'suggestion': 'Extraer de experiencia laboral y educación'
            })
        
        # Analizar experiencia
        if not candidate.get('experiencia') or len(candidate.get('experiencia', '').strip()) < 10:
            missing_fields.append({
                'field': 'experiencia',
                'label': 'Experiencia',
                'required': False,
                'current_value': candidate.get('experiencia'),
                'suggestion': 'Detallar experiencia laboral relevante'
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'candidate_id': candidate_id,
            'candidate_name': candidate.get('nombre_completo'),
            'missing_fields': missing_fields,
            'warnings': warnings,
            'completion_percentage': calculate_completion_percentage(candidate)
        })
        
    except Exception as e:
        app.logger.error(f"Error obteniendo campos faltantes: {str(e)}")
        return jsonify({'error': 'Error obteniendo campos faltantes'}), 500

def calculate_completion_percentage(candidate):
    """Calcular porcentaje de completitud del perfil"""
    total_fields = 10  # Campos importantes
    filled_fields = 0
    
    important_fields = [
        'nombre_completo', 'email', 'telefono', 'ciudad', 'cargo_solicitado',
        'experiencia', 'habilidades', 'grado_academico', 'fecha_nacimiento', 'nacionalidad'
    ]
    
    for field in important_fields:
        value = candidate.get(field)
        if value and str(value).strip() and value != 'null' and value != '[]':
            filled_fields += 1
    
    return round((filled_fields / total_fields) * 100, 1)

# =====================================================
# 📱 ENDPOINTS WHATSAPP MULTI-TENANT
# =====================================================

@app.route('/api/whatsapp/config', methods=['GET', 'POST', 'PUT', 'DELETE'])
@token_required
def handle_whatsapp_config():
    """Manejador de configuración de WhatsApp por tenant"""
    try:
        tenant_id = get_current_tenant_id()
        
        if request.method == 'GET':
            # Obtener configuración actual
            api_type = request.args.get('api_type')
            config = config_manager.get_tenant_config(tenant_id, api_type)
            
            if config:
                return jsonify({
                    'success': True,
                    'config': config
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Configuración no encontrada'
                }), 404
        
        elif request.method == 'POST':
            # Crear nueva configuración
            data = request.get_json()
            data['tenant_id'] = tenant_id
            
            success, message = config_manager.create_tenant_config(tenant_id, data)
            
            return jsonify({
                'success': success,
                'message': message
            }), 201 if success else 400
        
        elif request.method == 'PUT':
            # Actualizar configuración existente
            data = request.get_json()
            api_type = data.get('api_type')
            
            if not api_type:
                return jsonify({
                    'success': False,
                    'message': 'Tipo de API requerido'
                }), 400
            
            success, message = config_manager.update_tenant_config(tenant_id, api_type, data)
            
            return jsonify({
                'success': success,
                'message': message
            }), 200 if success else 400
        
        elif request.method == 'DELETE':
            # Eliminar configuración
            api_type = request.args.get('api_type')
            
            if not api_type:
                return jsonify({
                    'success': False,
                    'message': 'Tipo de API requerido'
                }), 400
            
            success, message = config_manager.delete_tenant_config(tenant_id, api_type)
            
            return jsonify({
                'success': success,
                'message': message
            }), 200 if success else 400
        
    except Exception as e:
        app.logger.error(f"Error en configuración WhatsApp: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@app.route('/api/whatsapp/config/test', methods=['POST'])
@token_required
def test_whatsapp_config():
    """Probar configuración de WhatsApp"""
    try:
        tenant_id = get_current_tenant_id()
        data = request.get_json()
        api_type = data.get('api_type')
        
        if not api_type:
            return jsonify({
                'success': False,
                'message': 'Tipo de API requerido'
            }), 400
        
        success, message = config_manager.test_tenant_config(tenant_id, api_type)
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 400
        
    except Exception as e:
        app.logger.error(f"Error probando configuración WhatsApp: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@app.route('/api/whatsapp/stats', methods=['GET'])
@token_required
def get_whatsapp_stats():
    """Obtener estadísticas de WhatsApp del tenant"""
    try:
        tenant_id = get_current_tenant_id()
        stats = config_manager.get_tenant_stats(tenant_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error obteniendo estadísticas WhatsApp: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@app.route('/api/whatsapp/conversations', methods=['GET'])
@token_required
def get_whatsapp_conversations():
    """Obtener conversaciones de WhatsApp del tenant"""
    try:
        tenant_id = get_current_tenant_id()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener conversaciones
        cursor.execute("""
            SELECT 
                id, conversation_id, contact_phone, contact_name,
                last_message_at, last_message_preview, unread_count,
                status, is_pinned, priority, created_at
            FROM WhatsApp_Conversations 
            WHERE tenant_id = %s 
            ORDER BY last_message_at DESC, created_at DESC
        """, (tenant_id,))
        
        conversations = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'conversations': conversations
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error obteniendo conversaciones WhatsApp: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@app.route('/api/whatsapp/conversations/<int:conversation_id>/messages', methods=['GET', 'POST'])
@token_required
def handle_conversation_messages(conversation_id):
    """Manejar mensajes de una conversación"""
    try:
        tenant_id = get_current_tenant_id()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar que la conversación pertenece al tenant
        cursor.execute("""
            SELECT id FROM WhatsApp_Conversations 
            WHERE id = %s AND tenant_id = %s
        """, (conversation_id, tenant_id))
        
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'message': 'Conversación no encontrada'
            }), 404
        
        if request.method == 'GET':
            # Obtener mensajes de la conversación
            cursor.execute("""
                SELECT 
                    id, message_id, direction, message_type, content,
                    media_url, status, timestamp, created_at
                FROM WhatsApp_Messages 
                WHERE conversation_id = %s 
                ORDER BY timestamp ASC, created_at ASC
            """, (conversation_id,))
            
            messages = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'messages': messages
            }), 200

        elif request.method == 'POST':
            # Enviar mensaje usando WhatsApp Business API
            data = request.get_json()
            message_content = data.get('message')
            message_type = data.get('type', 'text')
            reply_to_message_id = data.get('reply_to_message_id')
            media_url = data.get('media_url')
            caption = data.get('caption')
            template_name = data.get('template_name')
            template_params = data.get('template_params', [])
            
            if not message_content and not template_name:
                return jsonify({
                    'success': False,
                    'message': 'Contenido del mensaje o template requerido'
                }), 400
            
            # Obtener número de teléfono de la conversación
            cursor.execute("""
                SELECT wa_contact_phone FROM WhatsApp_Conversations 
                WHERE id = %s AND tenant_id = %s
            """, (conversation_id, tenant_id))
            
            conversation = cursor.fetchone()
            if not conversation:
                return jsonify({
                    'success': False,
                    'message': 'Conversación no encontrada'
                }), 404
            
            to_phone = conversation['wa_contact_phone']
            
            # Enviar mensaje usando la API oficial
            if message_type == 'template':
                result = send_whatsapp_message(
                    tenant_id=tenant_id,
                    to=to_phone,
                    message=template_name,
                    message_type='template',
                    template_params=template_params
                )
            elif message_type in ['image', 'document', 'audio', 'video']:
                result = send_whatsapp_message(
                    tenant_id=tenant_id,
                    to=to_phone,
                    message=message_type,
                    message_type=message_type,
                    media_url=media_url,
                    caption=caption
                )
            else:  # text
                result = send_whatsapp_message(
                    tenant_id=tenant_id,
                    to=to_phone,
                    message=message_content,
                    message_type='text',
                    reply_to_message_id=reply_to_message_id
                )
            
            if result['status'] == 'success':
                return jsonify({
                    'success': True,
                    'message': 'Mensaje enviado exitosamente',
                    'message_id': result.get('message_id'),
                    'whatsapp_response': result.get('response')
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': f'Error enviando mensaje: {result.get("error", "Error desconocido")}'
                }), 400
        
    except Exception as e:
        app.logger.error(f"Error manejando mensajes: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500
    
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/whatsapp/templates', methods=['GET', 'POST', 'PUT', 'DELETE'])
@token_required
def handle_whatsapp_templates_multi_tenant():
    """Manejar plantillas de WhatsApp del tenant"""
    try:
        tenant_id = get_current_tenant_id()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'GET':
            # Obtener plantillas del tenant
            cursor.execute("""
                SELECT 
                    id, name, category, subject, content, variables,
                    is_active, is_default, usage_count, last_used_at,
                    created_at, updated_at
                FROM WhatsApp_Templates 
                WHERE tenant_id = %s 
                ORDER BY category, name
            """, (tenant_id,))
            
            templates = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'templates': templates
            }), 200
        
        elif request.method == 'POST':
            # Crear nueva plantilla
            data = request.get_json()
            
            cursor.execute("""
                INSERT INTO WhatsApp_Templates (
                    tenant_id, name, category, subject, content, variables,
                    is_active, is_default, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tenant_id, data.get('name'), data.get('category'),
                data.get('subject'), data.get('content'),
                json.dumps(data.get('variables', [])),
                data.get('is_active', True), data.get('is_default', False),
                1  # Usuario por defecto
            ))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Plantilla creada exitosamente'
            }), 201
        
        elif request.method == 'PUT':
            # Actualizar plantilla
            template_id = request.args.get('id')
            data = request.get_json()
            
            if not template_id:
                return jsonify({
                    'success': False,
                    'message': 'ID de plantilla requerido'
                }), 400
            
            cursor.execute("""
                UPDATE WhatsApp_Templates 
                SET name = %s, category = %s, subject = %s, content = %s,
                    variables = %s, is_active = %s, is_default = %s,
                    updated_at = NOW()
                WHERE id = %s AND tenant_id = %s
            """, (
                data.get('name'), data.get('category'), data.get('subject'),
                data.get('content'), json.dumps(data.get('variables', [])),
                data.get('is_active'), data.get('is_default'),
                template_id, tenant_id
            ))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Plantilla actualizada exitosamente'
            }), 200

        elif request.method == 'DELETE':
            # Eliminar plantilla
            template_id = request.args.get('id')
            
            if not template_id:
                return jsonify({
                    'success': False,
                    'message': 'ID de plantilla requerido'
                }), 400
            
            cursor.execute("""
                DELETE FROM WhatsApp_Templates 
                WHERE id = %s AND tenant_id = %s AND is_default = FALSE
            """, (template_id, tenant_id))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Plantilla eliminada exitosamente'
            }), 200
        
    except Exception as e:
        app.logger.error(f"Error manejando plantillas WhatsApp: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500
    
    finally:
        if 'conn' in locals():
            conn.close()
        
# =====================================================
# =====================================================
# 📤 ENDPOINTS DE ENVÍO DIRECTO WHATSAPP (HÍBRIDO)
# =====================================================
@app.route('/api/whatsapp/send-message', methods=['POST'])
@token_required
def send_whatsapp_message_direct():
    """Enviar mensaje de WhatsApp directamente a un número"""
    try:
        tenant_id = get_current_tenant_id()
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['to', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido: {field}'
                }), 400
        
        to_phone = data['to']
        message_content = data['message']
        message_type = data.get('type', 'text')
        reply_to_message_id = data.get('reply_to_message_id')
        media_url = data.get('media_url')
        caption = data.get('caption')
        template_name = data.get('template_name')
        template_params = data.get('template_params', [])
        
        # Determinar el modo de WhatsApp para este tenant
        whatsapp_mode = get_tenant_whatsapp_mode(tenant_id)
        
        app.logger.info(f"Enviando mensaje para tenant {tenant_id} usando modo: {whatsapp_mode}")
        
        # Enviar mensaje según el modo configurado
        if whatsapp_mode == 'business_api':
            # Usar WhatsApp Business API oficial
            if message_type == 'template':
                result = send_whatsapp_message(
                    tenant_id=tenant_id,
                    to=to_phone,
                    message=template_name,
                    message_type='template',
                    template_params=template_params
                )
            elif message_type in ['image', 'document', 'audio', 'video']:
                result = send_whatsapp_message(
                    tenant_id=tenant_id,
                    to=to_phone,
                    message=message_type,
                    message_type=message_type,
                    media_url=media_url,
                    caption=caption
                )
            else:  # text
                result = send_whatsapp_message(
                    tenant_id=tenant_id,
                    to=to_phone,
                    message=message_content,
                    message_type='text',
                    reply_to_message_id=reply_to_message_id
                )
        else:
            # Usar WhatsApp Web.js
            if message_type == 'template':
                # Para templates en Web.js, enviar como texto
                template_text = f"Template: {template_name}"
                if template_params:
                    template_text += f" - Parámetros: {', '.join(template_params)}"
                result = send_whatsapp_web_message(
                    tenant_id=tenant_id,
                    to=to_phone,
                    message=template_text,
                    message_type='text'
                )
            else:
                result = send_whatsapp_web_message(
                    tenant_id=tenant_id,
                    to=to_phone,
                    message=message_content,
                    message_type=message_type,
                    media_url=media_url,
                    caption=caption
                )
        
        if result['status'] == 'success':
            return jsonify({
                'success': True,
                'message': 'Mensaje enviado exitosamente',
                'message_id': result.get('message_id'),
                'whatsapp_response': result.get('response')
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Error enviando mensaje: {result.get("error", "Error desconocido")}'
            }), 400
            
    except Exception as e:
        app.logger.error(f"Error enviando mensaje directo: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# =====================================================
# 📱 ENDPOINTS ESPECÍFICOS DE WHATSAPP WEB.JS
# =====================================================
@app.route('/api/whatsapp/web/init-session', methods=['POST'])
@token_required
def init_whatsapp_web_session():
    """Inicializar sesión de WhatsApp Web.js"""
    try:
        tenant_id = get_current_tenant_id()
        data = request.get_json()
        user_id = data.get('user_id', 1)  # Usuario por defecto
        
        result = initialize_whatsapp_web_session(tenant_id, user_id)
        
        return jsonify(result), 200 if result['status'] == 'success' else 400
        
    except Exception as e:
        app.logger.error(f"Error inicializando sesión Web: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@app.route('/api/whatsapp/web/session-status', methods=['GET'])
@token_required
def get_whatsapp_web_session_status():
    """Obtener estado de sesión de WhatsApp Web.js"""
    try:
        tenant_id = get_current_tenant_id()
        result = get_whatsapp_web_status(tenant_id)
        
        return jsonify(result), 200 if result['status'] == 'success' else 400
        
    except Exception as e:
        app.logger.error(f"Error obteniendo estado Web: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@app.route('/api/whatsapp/web/chats', methods=['GET'])
@token_required
def get_whatsapp_web_chats():
    """Obtener chats de WhatsApp Web.js"""
    try:
        tenant_id = get_current_tenant_id()
        result = web_manager.get_web_chats(tenant_id)
        
        return jsonify(result), 200 if result['status'] == 'success' else 400
        
    except Exception as e:
        app.logger.error(f"Error obteniendo chats Web: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@app.route('/api/whatsapp/web/close-session', methods=['DELETE'])
@token_required
def close_whatsapp_web_session():
    """Cerrar sesión de WhatsApp Web.js"""
    try:
        tenant_id = get_current_tenant_id()
        result = web_manager.close_web_session(tenant_id)
        
        return jsonify(result), 200 if result['status'] == 'success' else 400
        
    except Exception as e:
        app.logger.error(f"Error cerrando sesión Web: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@app.route('/api/whatsapp/mode', methods=['GET'])
@token_required
def get_whatsapp_mode():
    """Obtener el modo de WhatsApp configurado para el tenant"""
    try:
        tenant_id = get_current_tenant_id()
        mode = get_tenant_whatsapp_mode(tenant_id)
        
        return jsonify({
            'success': True,
            'mode': mode,
            'tenant_id': tenant_id,
            'description': {
                'business_api': 'WhatsApp Business API oficial',
                'web_js': 'WhatsApp Web.js (cuenta personal/empresarial)',
                'hybrid': 'Modo híbrido (ambos disponibles)'
            }.get(mode, 'Modo desconocido')
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error obteniendo modo WhatsApp: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@app.route('/api/whatsapp/message-status/<message_id>', methods=['GET'])
@token_required
def get_whatsapp_message_status_endpoint(message_id):
    """Obtener el estado de un mensaje enviado"""
    try:
        tenant_id = get_current_tenant_id()
        result = get_whatsapp_message_status(tenant_id, message_id)
        
        if result['status'] == 'success':
            return jsonify({
                'success': True,
                'message_status': result.get('message_status'),
                'timestamp': result.get('timestamp'),
                'error': result.get('error')
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Error obteniendo estado')
            }), 400
            
    except Exception as e:
        app.logger.error(f"Error obteniendo estado del mensaje: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# =====================================================
# 🔗 ENDPOINTS DE WEBHOOK WHATSAPP
# =====================================================

@app.route('/api/whatsapp/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """Manejador principal de webhooks de WhatsApp"""
    if request.method == 'GET':
        return handle_whatsapp_webhook_get()
    elif request.method == 'POST':
        return handle_whatsapp_webhook_post()

@app.route('/api/whatsapp/webhook/<int:tenant_id>', methods=['POST'])
def whatsapp_webhook_tenant(tenant_id):
    """Manejador específico por tenant para webhooks directos"""
    try:
        # Procesar webhook específico para un tenant
        webhook_data = request.get_json()
        
        # Log del webhook recibido
        app.logger.info(f"📨 Webhook específico recibido para tenant {tenant_id}")
        
        # Aquí podrías procesar el webhook específicamente para este tenant
        # Por ahora, redirigir al manejador principal
        
        return handle_whatsapp_webhook_post()
        
    except Exception as e:
        app.logger.error(f"❌ Error procesando webhook tenant {tenant_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ==================== ENDPOINTS DE OCI OBJECT STORAGE ====================

@app.route('/api/cv/upload-to-oci', methods=['POST'])
@token_required
def upload_cv_to_oci():
    """
    Subir CV individual a OCI Object Storage con procesamiento completo
    """
    if not OCI_SERVICES_AVAILABLE:
        return jsonify({'error': 'Servicios OCI no disponibles. Contacte al administrador.'}), 503
        
    try:
        tenant_id = get_current_tenant_id()
        user_id = g.current_user.get('id') or g.current_user.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Error de autenticación: ID de usuario no encontrado'}), 401
        
        # Verificar si hay archivo
        if 'file' not in request.files:
            return jsonify({'error': 'No se encontró archivo'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó archivo'}), 400
        
        # Validar tipo de archivo
        allowed_extensions = {'.pdf', '.docx', '.doc'}
        file_ext = os.path.splitext(file.filename.lower())[1]
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Tipo de archivo no soportado: {file_ext}. Solo se permiten PDF, DOCX y DOC.'}), 400
        
        # Obtener datos adicionales del formulario
        candidate_id = request.form.get('candidate_id')
        # Gemini AI es OBLIGATORIO para crear perfiles de candidatos
        force_process = True  # Siempre procesar con IA
        
        # Leer contenido del archivo
        file_content = file.read()
        
        # Generar identificador único para el CV
        cv_identifier = oci_storage_service.generate_cv_identifier(
            tenant_id=tenant_id,
            candidate_id=int(candidate_id) if candidate_id else None
        )
        
        # Subir archivo a OCI Object Storage
        upload_result = oci_storage_service.upload_cv(
            file_content=file_content,
            tenant_id=tenant_id,
            cv_identifier=cv_identifier,
            original_filename=file.filename,
            candidate_id=int(candidate_id) if candidate_id else None
        )
        
        if not upload_result['success']:
            return jsonify({
                'success': False,
                'error': f"Error subiendo archivo a OCI: {upload_result['error']}"
            }), 500
        
        # Crear PAR para acceso al archivo
        par_result = oci_storage_service.create_par(
            object_key=upload_result['object_key'],
            cv_identifier=cv_identifier
        )
        
        if not par_result['success']:
            return jsonify({
                'success': False,
                'error': f"Error creando PAR: {par_result['error']}"
            }), 500
        
        # Procesar CV con Gemini AI (OBLIGATORIO para crear perfiles)
        processed_data = None
        try:
            # Extraer texto del CV
            cv_text = cv_processing_service.extract_text_from_file(
                file_content=file_content,
                filename=file.filename
            )
            
            # Procesar con Gemini
            gemini_result = cv_processing_service.process_cv_with_gemini(
                cv_text=cv_text,
                tenant_id=tenant_id
            )
            
            if gemini_result['success']:
                # Validar datos procesados
                validation_result = cv_processing_service.validate_cv_data(
                    gemini_result['data']
                )
                
                if validation_result['success']:
                    processed_data = validation_result['validated_data']
                else:
                    app.logger.warning(f"Error validando datos del CV: {validation_result['error']}")
                    # Si falla la validación, es un error crítico
                    return jsonify({
                        'success': False,
                        'error': f"Error validando datos extraídos: {validation_result['error']}"
                    }), 500
            else:
                app.logger.error(f"Error procesando CV con Gemini: {gemini_result['error']}")
                # Si falla el procesamiento con IA, es un error crítico
                return jsonify({
                    'success': False,
                    'error': f"Error procesando CV con IA: {gemini_result['error']}"
                }), 500
                
        except Exception as e:
            app.logger.error(f"Error procesando CV: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"Error procesando CV: {str(e)}"
            }), 500
        
        # Preparar respuesta
        response_data = {
            'success': True,
            'cv_identifier': cv_identifier,
            'file_info': {
                'original_name': file.filename,
                'size': upload_result['size'],
                'mime_type': upload_result['mime_type'],
                'object_key': upload_result['object_key']
            },
            'access_info': {
                'file_url': par_result['access_uri'],
                'expiration_date': par_result['expiration_date'],
                'par_id': par_result['par_id']
            }
        }
        
        # Agregar datos procesados si están disponibles
        if processed_data:
            response_data['processed_data'] = processed_data
        
        app.logger.info(f"CV subido exitosamente: {cv_identifier}")
        
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"Error en upload_cv_to_oci: {str(e)}")
        return jsonify({'error': 'Error al procesar CV'}), 500

@app.route('/api/cv/process-existing/<cv_identifier>', methods=['POST'])
@token_required
def process_existing_cv(cv_identifier):
    """
    Procesar un CV existente en OCI con Gemini AI
    """
    try:
        tenant_id = get_current_tenant_id()
        
        # Obtener información del CV desde la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM CV_Processing_Logs 
            WHERE tenant_id = %s AND cv_identifier = %s
        """, (tenant_id, cv_identifier))
        
        cv_record = cursor.fetchone()
        
        if not cv_record:
            return jsonify({'error': 'CV no encontrado'}), 404
        
        # Obtener archivo de OCI
        object_info = oci_storage_service.get_object_info(cv_record['file_url'])
        
        if not object_info['success']:
            return jsonify({'error': 'Error obteniendo archivo de OCI'}), 500
        
        # Descargar archivo para procesamiento
        # Nota: En un entorno real, necesitarías implementar la descarga desde OCI
        # Por ahora, asumimos que el archivo está disponible localmente
        
        # Procesar con Gemini
        try:
            # Aquí necesitarías descargar el archivo desde OCI
            # Por simplicidad, asumimos que tienes acceso al contenido
            
            # Simular extracción de texto (en implementación real, descargarías el archivo)
            cv_text = "Texto del CV extraído..."  # Placeholder
            
            gemini_result = cv_processing_service.process_cv_with_gemini(
                cv_text=cv_text,
                tenant_id=tenant_id
            )
            
            if gemini_result['success']:
                # Validar datos procesados
                validation_result = cv_processing_service.validate_cv_data(
                    gemini_result['data']
                )
                
                if validation_result['success']:
                    # Actualizar registro en base de datos con datos procesados
                    cursor.execute("""
                        UPDATE CV_Processing_Logs 
                        SET processed_data = %s, 
                            processing_status = 'completed',
                            created_at = NOW()
                        WHERE tenant_id = %s AND cv_identifier = %s
                    """, (json.dumps(validation_result['validated_data']), tenant_id, cv_identifier))
                    
                    conn.commit()
                    
                    return jsonify({
                        'success': True,
                        'processed_data': validation_result['validated_data'],
                        'message': 'CV procesado exitosamente'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f"Error validando datos: {validation_result['error']}"
                    }), 400
            else:
                return jsonify({
                    'success': False,
                    'error': f"Error procesando con Gemini: {gemini_result['error']}"
                }), 500
                
        except Exception as e:
            app.logger.error(f"Error procesando CV existente: {str(e)}")
            return jsonify({'error': 'Error procesando CV'}), 500
            
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        app.logger.error(f"Error en process_existing_cv: {str(e)}")
        return jsonify({'error': 'Error al procesar CV'}), 500

@app.route('/api/cv/download/<cv_identifier>', methods=['GET'])
@token_required
def download_cv(cv_identifier):
    """
    Descargar CV usando PAR de OCI
    """
    try:
        tenant_id = get_current_tenant_id()
        
        # Obtener información del CV desde la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT file_url, original_filename, mime_type 
            FROM CV_Processing_Logs 
            WHERE tenant_id = %s AND cv_identifier = %s
        """, (tenant_id, cv_identifier))
        
        cv_record = cursor.fetchone()
        
        if not cv_record:
            return jsonify({'error': 'CV no encontrado'}), 404
        
        # La PAR ya contiene la URL completa para acceso directo
        file_url = cv_record['file_url']
        
        cursor.close()
        conn.close()
        
        # Redirigir al archivo en OCI
        return redirect(file_url)
        
    except Exception as e:
        app.logger.error(f"Error en download_cv: {str(e)}")
        return jsonify({'error': 'Error al descargar CV'}), 500

@app.route('/api/cv/bulk-upload', methods=['POST'])
@token_required
def bulk_upload_cvs_to_oci():
    """
    Subir múltiples CVs (hasta 100) a OCI Object Storage con procesamiento en lotes
    """
    if not OCI_SERVICES_AVAILABLE:
        return jsonify({'error': 'Servicios OCI no disponibles. Contacte al administrador.'}), 503
        
    try:
        tenant_id = get_current_tenant_id()
        user_id = g.current_user.get('id') or g.current_user.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Error de autenticación: ID de usuario no encontrado'}), 401
        
        # Verificar si hay archivos
        if 'files' not in request.files:
            return jsonify({'error': 'No se encontraron archivos'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No se seleccionaron archivos válidos'}), 400
        
        # Validar límite de archivos
        if len(files) > 100:
            return jsonify({'error': 'Máximo 100 archivos por lote'}), 400
        
        # Validar tipos de archivo y tamaños
        allowed_extensions = {'.pdf', '.docx', '.doc'}
        valid_files = []
        total_size = 0
        max_file_size = 50 * 1024 * 1024  # 50MB por archivo
        
        for file in files:
            if file.filename:
                file_ext = os.path.splitext(file.filename.lower())[1]
                if file_ext not in allowed_extensions:
                    return jsonify({'error': f'Tipo de archivo no soportado: {file_ext}. Solo se permiten PDF, DOCX y DOC.'}), 400
                
                # Verificar tamaño del archivo
                file_content = file.read()
                file_size = len(file_content)
                
                if file_size > max_file_size:
                    return jsonify({'error': f'Archivo {file.filename} excede el límite de 50MB'}), 400
                
                total_size += file_size
                
                # Resetear posición del archivo
                file.seek(0)
                
                valid_files.append({
                    'file': file,
                    'content': file_content,
                    'filename': file.filename,
                    'size': file_size
                })
        
        # Verificar tamaño total
        max_total_size = 500 * 1024 * 1024  # 500MB total por lote
        if total_size > max_total_size:
            return jsonify({'error': 'El tamaño total de los archivos excede 500MB'}), 400
        
        # Crear trabajo de procesamiento masivo
        job_id = f"bulk_upload_{tenant_id}_{user_id}_{int(time.time())}"
        
        # Procesar archivos en lotes de 10 para evitar sobrecarga
        batch_size = 10
        results = []
        errors = []
        
        for i in range(0, len(valid_files), batch_size):
            batch = valid_files[i:i + batch_size]
            batch_results = []
            
            for file_data in batch:
                try:
                    # Generar identificador único para el CV
                    cv_identifier = oci_storage_service.generate_cv_identifier(
                        tenant_id=tenant_id,
                        candidate_id=None  # Se determinará después del procesamiento
                    )
                    
                    # Subir archivo a OCI Object Storage
                    upload_result = oci_storage_service.upload_cv(
                        file_content=file_data['content'],
                        tenant_id=tenant_id,
                        cv_identifier=cv_identifier,
                        original_filename=file_data['filename'],
                        candidate_id=None
                    )
                    
                    if not upload_result['success']:
                        errors.append({
                            'filename': file_data['filename'],
                            'error': f"Error subiendo a OCI: {upload_result['error']}"
                        })
                        continue
                    
                    # Crear PAR para acceso al archivo
                    par_result = oci_storage_service.create_par(
                        object_key=upload_result['object_key'],
                        cv_identifier=cv_identifier
                    )
                    
                    if not par_result['success']:
                        errors.append({
                            'filename': file_data['filename'],
                            'error': f"Error creando PAR: {par_result['error']}"
                        })
                        continue
                    
                    # Procesar CV con Gemini AI (OBLIGATORIO)
                    try:
                        # Extraer texto del CV
                        cv_text = cv_processing_service.extract_text_from_file(
                            file_content=file_data['content'],
                            filename=file_data['filename']
                        )
                        
                        # Procesar con Gemini
                        gemini_result = cv_processing_service.process_cv_with_gemini(
                            cv_text=cv_text,
                            tenant_id=tenant_id
                        )
                        
                        if gemini_result['success']:
                            # Validar datos procesados
                            validation_result = cv_processing_service.validate_cv_data(
                                gemini_result['data']
                            )
                            
                            if validation_result['success']:
                                processed_data = validation_result['validated_data']
                                
                                # Crear candidato en base de datos
                                candidate_id = create_candidate_from_cv_data(
                                    processed_data, tenant_id, user_id
                                )
                                
                                # Guardar información del CV en base de datos
                                save_cv_to_database(
                                    tenant_id=tenant_id,
                                    candidate_id=candidate_id,
                                    cv_identifier=cv_identifier,
                                    original_filename=file_data['filename'],
                                    object_key=upload_result['object_key'],
                                    file_url=par_result['access_uri'],
                                    par_id=par_result['par_id'],
                                    mime_type=upload_result['mime_type'],
                                    file_size=upload_result['size'],
                                    processed_data=processed_data
                                )
                                
                                batch_results.append({
                                    'filename': file_data['filename'],
                                    'success': True,
                                    'cv_identifier': cv_identifier,
                                    'candidate_id': candidate_id,
                                    'processed_data': processed_data
                                })
                                
                            else:
                                errors.append({
                                    'filename': file_data['filename'],
                                    'error': f"Error validando datos: {validation_result['error']}"
                                })
                        else:
                            errors.append({
                                'filename': file_data['filename'],
                                'error': f"Error procesando con IA: {gemini_result['error']}"
                            })
                            
                    except Exception as e:
                        errors.append({
                            'filename': file_data['filename'],
                            'error': f"Error procesando CV: {str(e)}"
                        })
                        
                except Exception as e:
                    errors.append({
                        'filename': file_data['filename'],
                        'error': f"Error general: {str(e)}"
                    })
            
            results.extend(batch_results)
            
            # Pequeña pausa entre lotes para evitar sobrecarga
            time.sleep(1)
        
        # Preparar respuesta
        response_data = {
            'success': True,
            'job_id': job_id,
            'summary': {
                'total_files': len(valid_files),
                'successful': len(results),
                'errors': len(errors),
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            },
            'results': results,
            'errors': errors
        }
        
        app.logger.info(f"Carga masiva completada: {len(results)} exitosos, {len(errors)} errores")
        
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"Error en bulk_upload_cvs_to_oci: {str(e)}")
        return jsonify({'error': 'Error al procesar carga masiva'}), 500

def create_candidate_from_cv_data(cv_data, tenant_id, user_id):
    """
    Crear candidato en base de datos a partir de datos extraídos por IA
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        personal_info = cv_data.get('personal_info', {})
        experiencia = cv_data.get('experiencia', {})
        habilidades = cv_data.get('habilidades', {})
        
        # Extraer información personal
        nombre_completo = personal_info.get('nombre_completo', 'Candidato Sin Nombre')
        email = personal_info.get('email', '')
        telefono = personal_info.get('telefono', '')
        ciudad = personal_info.get('ciudad', '')
        pais = personal_info.get('pais', '')
        
        # Extraer experiencia
        años_experiencia = experiencia.get('años_experiencia', 0)
        if isinstance(años_experiencia, str):
            try:
                años_experiencia = float(años_experiencia)
            except ValueError:
                años_experiencia = 0
        
        # Crear resumen de experiencia
        experiencia_detallada = experiencia.get('experiencia_detallada', [])
        experiencia_texto = ""
        if experiencia_detallada:
            for exp in experiencia_detallada[:3]:  # Solo las primeras 3 experiencias
                empresa = exp.get('empresa', '')
                posicion = exp.get('posicion', '')
                if empresa and posicion:
                    experiencia_texto += f"{posicion} en {empresa}, "
            experiencia_texto = experiencia_texto.rstrip(', ')
        
        # Crear resumen de habilidades
        habilidades_tecnicas = habilidades.get('tecnicas', [])
        habilidades_texto = ", ".join(habilidades_tecnicas[:10])  # Máximo 10 habilidades
        
        # Insertar candidato en tabla Afiliados
        cursor.execute("""
            INSERT INTO Afiliados (
                tenant_id, nombre_completo, email, telefono, ciudad,
                experiencia, habilidades, estado, fecha_registro
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, 'Activo', NOW()
            )
        """, (
            tenant_id, nombre_completo, email, telefono, ciudad,
            experiencia_texto, habilidades_texto
        ))
        
        candidate_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        app.logger.info(f"Candidato creado: ID {candidate_id} para tenant {tenant_id}")
        return candidate_id
        
    except Exception as e:
        app.logger.error(f"Error creando candidato: {str(e)}")
        raise

def save_cv_to_database(tenant_id, candidate_id, cv_identifier, original_filename, 
                       object_key, file_url, par_id, mime_type, file_size, processed_data):
    """
    Actualizar información del CV en tabla Afiliados
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Actualizar el registro del candidato con la información del CV
        cursor.execute("""
            UPDATE Afiliados 
            SET cv_url = %s, 
                ultima_actualizacion = NOW()
            WHERE id_afiliado = %s AND tenant_id = %s
        """, (file_url, candidate_id, tenant_id))
        
        # Registrar en log de procesamiento
        cursor.execute("""
            INSERT INTO CV_Processing_Logs (
                tenant_id, candidate_id, cv_identifier, original_filename,
                object_key, file_url, par_id, mime_type, file_size,
                processing_status, processed_data, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, 'completed', %s, NOW()
            )
        """, (
            tenant_id, candidate_id, cv_identifier, original_filename,
            object_key, file_url, par_id, mime_type, file_size,
            json.dumps(processed_data)
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        app.logger.info(f"CV guardado en Afiliados: {cv_identifier} para candidato {candidate_id}")
        
    except Exception as e:
        app.logger.error(f"Error guardando CV en Afiliados: {str(e)}")
        raise

@app.route('/api/cv/delete/<cv_identifier>', methods=['DELETE'])
@token_required
def delete_cv_from_oci(cv_identifier):
    """
    Eliminar CV de OCI Object Storage y base de datos
    """
    try:
        tenant_id = get_current_tenant_id()
        user_id = g.current_user.get('id') or g.current_user.get('user_id')
        
        # Obtener información del CV desde la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT object_key, file_url 
            FROM CV_Processing_Logs 
            WHERE tenant_id = %s AND cv_identifier = %s
        """, (tenant_id, cv_identifier))
        
        cv_record = cursor.fetchone()
        
        if not cv_record:
            return jsonify({'error': 'CV no encontrado'}), 404
        
        # Eliminar archivo de OCI
        delete_result = oci_storage_service.delete_object(cv_record['object_key'])
        
        if not delete_result['success']:
            app.logger.warning(f"Error eliminando archivo de OCI: {delete_result['error']}")
        
        # Eliminar registro de logs y limpiar cv_url en Afiliados
        cursor.execute("""
            UPDATE Afiliados 
            SET cv_url = NULL, ultima_actualizacion = NOW()
            WHERE tenant_id = %s AND cv_url = %s
        """, (tenant_id, cv_record['file_url']))
        
        cursor.execute("""
            DELETE FROM CV_Processing_Logs 
            WHERE tenant_id = %s AND cv_identifier = %s
        """, (tenant_id, cv_identifier))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        app.logger.info(f"CV eliminado: {cv_identifier}")
        
        return jsonify({
            'success': True,
            'message': 'CV eliminado exitosamente'
        })
        
    except Exception as e:
        app.logger.error(f"Error en delete_cv_from_oci: {str(e)}")
        return jsonify({'error': 'Error al eliminar CV'}), 500

# --- PUNTO DE ENTRADA PARA EJECUTAR EL SERVIDOR (SIN CAMBIOS) ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
