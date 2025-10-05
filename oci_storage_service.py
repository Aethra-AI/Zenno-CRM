"""
OCI Object Storage Service para almacenamiento de CVs
"""
import os
import json
import uuid
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import logging

# Importaciones opcionales para OCI
try:
    import oci
    from oci.object_storage import ObjectStorageClient
    from oci.object_storage.models import CreatePreauthenticatedRequestDetails
    from oci.exceptions import ServiceError
    OCI_AVAILABLE = True
except ImportError:
    OCI_AVAILABLE = False
    oci = None
    ObjectStorageClient = None
    CreatePreauthenticatedRequestDetails = None
    ServiceError = Exception

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCIStorageService:
    """Servicio para manejar archivos en OCI Object Storage"""
    
    def __init__(self):
        """Inicializar cliente de OCI"""
        if not OCI_AVAILABLE:
            logger.error("OCI SDK no está disponible. Instale con: pip install oci")
            raise ImportError("OCI SDK no está disponible")
            
        try:
            # Configuración de OCI
            self.config = oci.config.from_file()
            self.object_storage_client = ObjectStorageClient(self.config)
            
            # Configuración del bucket (desde variables de entorno)
            self.namespace = os.getenv('OCI_NAMESPACE')
            self.bucket_name = os.getenv('OCI_BUCKET_NAME', 'crm-cvs')
            self.region = os.getenv('OCI_REGION', 'us-ashburn-1')
            
            logger.info(f"OCI Storage Service inicializado - Namespace: {self.namespace}, Bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Error inicializando OCI Storage Service: {str(e)}")
            raise
    
    def generate_cv_identifier(self, tenant_id: int, candidate_id: Optional[int] = None) -> str:
        """
        Generar identificador único para CV
        
        Args:
            tenant_id: ID del tenant
            candidate_id: ID del candidato (opcional)
            
        Returns:
            str: Identificador único en formato: tenant_{tenant_id}_cv_{uuid}
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        if candidate_id:
            return f"tenant_{tenant_id}_candidate_{candidate_id}_cv_{timestamp}_{unique_id}"
        else:
            return f"tenant_{tenant_id}_cv_{timestamp}_{unique_id}"
    
    def get_object_key(self, tenant_id: int, cv_identifier: str, original_filename: str) -> str:
        """
        Generar clave del objeto en OCI
        
        Args:
            tenant_id: ID del tenant
            cv_identifier: Identificador único del CV
            original_filename: Nombre original del archivo
            
        Returns:
            str: Clave del objeto
        """
        # Extraer extensión del archivo
        _, ext = os.path.splitext(original_filename)
        
        # Estructura: tenants/{tenant_id}/cvs/{cv_identifier}{ext}
        return f"tenants/{tenant_id}/cvs/{cv_identifier}{ext}"
    
    def upload_cv(
        self, 
        file_content: bytes, 
        tenant_id: int, 
        cv_identifier: str, 
        original_filename: str,
        candidate_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Subir CV a OCI Object Storage
        
        Args:
            file_content: Contenido del archivo
            tenant_id: ID del tenant
            cv_identifier: Identificador único del CV
            original_filename: Nombre original del archivo
            candidate_id: ID del candidato (opcional)
            
        Returns:
            Dict con información del archivo subido
        """
        try:
            # Generar clave del objeto
            object_key = self.get_object_key(tenant_id, cv_identifier, original_filename)
            
            # Detectar MIME type
            mime_type, _ = mimetypes.guess_type(original_filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Subir archivo
            logger.info(f"Subiendo CV: {object_key}")
            
            put_object_response = self.object_storage_client.put_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                object_name=object_key,
                put_object_body=file_content,
                content_type=mime_type
            )
            
            logger.info(f"CV subido exitosamente: {object_key}")
            
            return {
                'success': True,
                'object_key': object_key,
                'cv_identifier': cv_identifier,
                'mime_type': mime_type,
                'size': len(file_content),
                'etag': put_object_response.headers.get('etag'),
                'namespace': self.namespace,
                'bucket': self.bucket_name
            }
            
        except ServiceError as e:
            logger.error(f"Error de OCI al subir CV: {str(e)}")
            return {
                'success': False,
                'error': f"Error de OCI: {str(e)}",
                'error_code': e.status
            }
        except Exception as e:
            logger.error(f"Error general al subir CV: {str(e)}")
            return {
                'success': False,
                'error': f"Error general: {str(e)}"
            }
    
    def create_par(
        self, 
        object_key: str, 
        cv_identifier: str,
        expiration_years: int = 10
    ) -> Dict[str, Any]:
        """
        Crear Pre-Authenticated Request (PAR) para acceso al archivo
        
        Args:
            object_key: Clave del objeto en OCI
            cv_identifier: Identificador único del CV
            expiration_years: Años de expiración (default: 10)
            
        Returns:
            Dict con información de la PAR
        """
        try:
            # Calcular fecha de expiración
            expiration_date = datetime.now() + timedelta(days=expiration_years * 365)
            
            # Crear detalles de la PAR
            par_details = CreatePreauthenticatedRequestDetails(
                name=f"PAR_CV_{cv_identifier}",
                access_type="ObjectRead",
                time_expires=expiration_date,
                object_name=object_key
            )
            
            # Crear PAR
            logger.info(f"Creando PAR para: {object_key}")
            
            create_par_response = self.object_storage_client.create_preauthenticated_request(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                create_preauthenticated_request_details=par_details
            )
            
            # Construir URL completa de acceso
            access_uri = f"https://objectstorage.{self.region}.oraclecloud.com{create_par_response.data.full_path}"
            
            logger.info(f"PAR creada exitosamente: {access_uri}")
            
            return {
                'success': True,
                'par_id': create_par_response.data.id,
                'access_uri': access_uri,
                'expiration_date': expiration_date.isoformat(),
                'full_path': create_par_response.data.full_path
            }
            
        except ServiceError as e:
            logger.error(f"Error de OCI al crear PAR: {str(e)}")
            return {
                'success': False,
                'error': f"Error de OCI: {str(e)}",
                'error_code': e.status
            }
        except Exception as e:
            logger.error(f"Error general al crear PAR: {str(e)}")
            return {
                'success': False,
                'error': f"Error general: {str(e)}"
            }
    
    def delete_object(self, object_key: str) -> Dict[str, Any]:
        """
        Eliminar objeto de OCI Object Storage
        
        Args:
            object_key: Clave del objeto a eliminar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            logger.info(f"Eliminando objeto: {object_key}")
            
            self.object_storage_client.delete_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                object_name=object_key
            )
            
            logger.info(f"Objeto eliminado exitosamente: {object_key}")
            
            return {
                'success': True,
                'message': f"Objeto {object_key} eliminado exitosamente"
            }
            
        except ServiceError as e:
            logger.error(f"Error de OCI al eliminar objeto: {str(e)}")
            return {
                'success': False,
                'error': f"Error de OCI: {str(e)}",
                'error_code': e.status
            }
        except Exception as e:
            logger.error(f"Error general al eliminar objeto: {str(e)}")
            return {
                'success': False,
                'error': f"Error general: {str(e)}"
            }
    
    def get_object_info(self, object_key: str) -> Dict[str, Any]:
        """
        Obtener información de un objeto
        
        Args:
            object_key: Clave del objeto
            
        Returns:
            Dict con información del objeto
        """
        try:
            head_object_response = self.object_storage_client.head_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                object_name=object_key
            )
            
            return {
                'success': True,
                'size': head_object_response.headers.get('content-length'),
                'mime_type': head_object_response.headers.get('content-type'),
                'last_modified': head_object_response.headers.get('last-modified'),
                'etag': head_object_response.headers.get('etag'),
                'metadata': dict(head_object_response.headers)
            }
            
        except ServiceError as e:
            logger.error(f"Error de OCI al obtener info del objeto: {str(e)}")
            return {
                'success': False,
                'error': f"Error de OCI: {str(e)}",
                'error_code': e.status
            }
        except Exception as e:
            logger.error(f"Error general al obtener info del objeto: {str(e)}")
            return {
                'success': False,
                'error': f"Error general: {str(e)}"
            }

# Instancia global del servicio
oci_storage_service = OCIStorageService()

