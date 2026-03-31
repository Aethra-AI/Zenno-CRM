# Guía de Implementación: Sistema de Almacenamiento de CVs con OCI Object Storage

## 📋 Resumen del Sistema

Este sistema implementa un almacenamiento robusto y escalable de CVs utilizando Oracle Cloud Infrastructure (OCI) Object Storage, con procesamiento automático de IA usando Gemini y generación de URLs de acceso seguras (PAR).

### 🔄 Flujo del Sistema

```
1. Usuario sube CV → 2. Procesamiento OBLIGATORIO con Gemini AI → 3. Creación de perfil de candidato → 4. Almacenamiento en OCI → 5. Generación de PAR → 6. Almacenamiento en BD
```

## 🏗️ Arquitectura

### Backend (Python/Flask)
- **`oci_storage_service.py`**: Servicio principal para OCI Object Storage
- **`cv_processing_service.py`**: Procesamiento de CVs con Gemini AI
- **Rutas API**: Endpoints para upload, download, delete y process
- **Base de datos**: Tablas para metadatos y logs

### Frontend (React/TypeScript)
- **`OCIUploadModal.tsx`**: Modal para subida de CVs
- **`CVManager.tsx`**: Gestión y visualización de CVs almacenados
- **Integración**: Componentes responsivos para móvil y desktop

## 🚀 Instalación y Configuración

### 1. Dependencias Backend

```bash
# Instalar dependencias de Python
pip install -r requirements_oci.txt

# Dependencias principales:
# - oci==2.119.0
# - PyPDF2==3.0.1
# - python-docx==1.1.0
```

### 2. Configuración OCI

#### 2.1 Configurar OCI CLI
```bash
# Instalar OCI CLI
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Configurar credenciales
oci setup config

# Verificar configuración
oci iam user get --user-id $USER_OCID
```

#### 2.2 Variables de Entorno (.env)
```bash
# OCI Object Storage Configuration
OCI_NAMESPACE=your-namespace-name
OCI_BUCKET_NAME=crm-cvs
OCI_REGION=us-ashburn-1

# Gemini AI Configuration
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent

# Configuración adicional
MAX_FILE_SIZE_MB=50
PAR_EXPIRATION_YEARS=10
AUTO_PROCESS_CVS=true
```

#### 2.3 Configuración de Archivo OCI (~/.oci/config)
```ini
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaa...
fingerprint=aa:bb:cc:dd:ee:ff:gg:hh:ii:jj:kk:ll:mm:nn:oo:pp
key_file=~/.oci/oci_api_key.pem
tenancy=ocid1.tenancy.oc1..aaaaaaaa...
region=us-ashburn-1
```

### 3. Base de Datos

```bash
# Ejecutar script SQL
mysql -u username -p database_name < create_cv_tables.sql
```

### 4. Crear Bucket en OCI

```bash
# Crear bucket
oci os bucket create --namespace $OCI_NAMESPACE --name crm-cvs --compartment-id $COMPARTMENT_OCID

# Verificar bucket
oci os bucket get --namespace $OCI_NAMESPACE --name crm-cvs
```

## 📁 Estructura de Archivos

### Estructura en OCI Object Storage
```
Bucket: crm-cvs
├── tenants/
│   ├── 1/
│   │   └── cvs/
│   │       ├── tenant_1_cv_20241201_123456_abc123.pdf
│   │       └── tenant_1_candidate_5_cv_20241201_123456_def456.docx
│   ├── 2/
│   │   └── cvs/
│   │       └── tenant_2_cv_20241201_123456_ghi789.pdf
│   └── ...
```

### Identificadores de CV
- **Formato**: `tenant_{tenant_id}_cv_{timestamp}_{unique_id}`
- **Con candidato**: `tenant_{tenant_id}_candidate_{candidate_id}_cv_{timestamp}_{unique_id}`
- **Ejemplo**: `tenant_1_cv_20241201_123456_abc123`

## 🔧 API Endpoints

### 1. Subir CV Individual
```http
POST /api/cv/upload-to-oci
Content-Type: multipart/form-data
Authorization: Bearer {token}

Body:
- file: archivo CV
- candidate_id: ID del candidato (opcional)
- force_process: true/false (procesar con IA)
```

**Respuesta:**
```json
{
  "success": true,
  "cv_identifier": "tenant_1_cv_20241201_123456_abc123",
  "file_info": {
    "original_name": "cv_juan_perez.pdf",
    "size": 1024000,
    "mime_type": "application/pdf",
    "object_key": "tenants/1/cvs/tenant_1_cv_20241201_123456_abc123.pdf"
  },
  "access_info": {
    "file_url": "https://objectstorage.us-ashburn-1.oraclecloud.com/p/n/namespace/b/crm-cvs/o/tenants/1/cvs/tenant_1_cv_20241201_123456_abc123.pdf",
    "expiration_date": "2034-12-01T12:34:56Z",
    "par_id": "par-abc123"
  },
  "processed_data": {
    "personal_info": { ... },
    "experiencia": { ... },
    "habilidades": { ... }
  }
}
```

### 2. Procesar CV Existente
```http
POST /api/cv/process-existing/{cv_identifier}
Authorization: Bearer {token}
```

### 3. Descargar CV
```http
GET /api/cv/download/{cv_identifier}
Authorization: Bearer {token}
```

### 4. Eliminar CV
```http
DELETE /api/cv/delete/{cv_identifier}
Authorization: Bearer {token}
```

### 5. Carga Masiva (hasta 100 archivos)
```http
POST /api/cv/bulk-upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

Body:
- files: array de archivos CV (máx. 100 archivos, 50MB cada uno, 500MB total)
```

**Respuesta:**
```json
{
  "success": true,
  "job_id": "bulk_upload_1_123_1701234567",
  "summary": {
    "total_files": 25,
    "successful": 23,
    "errors": 2,
    "total_size_mb": 45.2
  },
  "results": [
    {
      "filename": "cv_juan_perez.pdf",
      "success": true,
      "cv_identifier": "tenant_1_cv_20241201_123456_abc123",
      "candidate_id": 456,
      "processed_data": { ... }
    }
  ],
  "errors": [
    {
      "filename": "cv_mal_formato.txt",
      "error": "Tipo de archivo no soportado"
    }
  ]
}
```

## 🔐 Seguridad y Acceso

### Pre-Authenticated Requests (PAR)
- **Duración**: 10 años por defecto
- **Acceso**: Solo lectura (ObjectRead)
- **URL**: Generada automáticamente por OCI
- **Seguridad**: URLs firmadas, no requieren autenticación adicional

### Aislamiento por Tenant
- Cada tenant tiene su propia carpeta en OCI
- Filtrado automático por `tenant_id`
- No hay acceso cruzado entre tenants

## 🤖 Procesamiento con IA

### Gemini AI Integration
- **Extracción de texto**: PDF, DOCX, DOC
- **Análisis estructurado**: Información personal, experiencia, habilidades
- **Validación de datos**: Limpieza y verificación
- **Formato JSON**: Datos estructurados para el CRM

### Estructura de Datos Extraídos
```json
{
  "personal_info": {
    "nombre_completo": "string",
    "email": "string",
    "telefono": "string",
    "ciudad": "string",
    "pais": "string"
  },
  "experiencia": {
    "años_experiencia": "number",
    "experiencia_detallada": [...]
  },
  "habilidades": {
    "tecnicas": ["array"],
    "blandas": ["array"],
    "idiomas": ["array"]
  },
  "metadata": {
    "calidad_datos": "string",
    "completitud": "number",
    "confiabilidad": "string"
  }
}
```

## 📊 Monitoreo y Logs

### Tablas de Base de Datos
- **`Candidatos_CVs`**: Metadatos de CVs almacenados
- **`CV_Processing_Logs`**: Logs de procesamiento
- **`Tenant_OCI_Config`**: Configuración por tenant

### Logs de Procesamiento
```sql
SELECT * FROM CV_Processing_Logs 
WHERE tenant_id = ? 
ORDER BY created_at DESC;
```

### Métricas Disponibles
- Total de CVs por tenant
- Tasa de éxito de procesamiento
- Tiempo promedio de procesamiento
- Uso de almacenamiento

## 🚨 Troubleshooting

### Errores Comunes

#### 1. Error de Configuración OCI
```
Error: OCI configuration not found
```
**Solución**: Verificar archivo `~/.oci/config` y variables de entorno

#### 2. Error de Permisos
```
Error: ServiceError 403 - Not authorized
```
**Solución**: Verificar políticas IAM y permisos de usuario

#### 3. Error de Procesamiento Gemini
```
Error: Gemini API key not found
```
**Solución**: Verificar variable `GEMINI_API_KEY` en `.env`

#### 4. Error de Archivo No Encontrado
```
Error: CV not found
```
**Solución**: Verificar `cv_identifier` y permisos de tenant

### Logs de Debug
```bash
# Ver logs del backend
tail -f /var/log/whatsapp-backend.log

# Ver logs de OCI
oci os object list --namespace $OCI_NAMESPACE --bucket-name crm-cvs
```

## 🔄 Mantenimiento

### Limpieza Automática
```sql
-- Procedimiento para limpiar CVs antiguos
CALL CleanupExpiredCVs();

-- Evento programado (opcional)
CREATE EVENT cleanup_cvs_event
ON SCHEDULE EVERY 1 MONTH
DO CALL CleanupExpiredCVs();
```

### Backup y Recuperación
- **OCI Object Storage**: Replicación automática
- **Base de datos**: Backup regular de metadatos
- **PARs**: Renovación automática si es necesario

## 📈 Optimizaciones Futuras

### 1. Compresión de Archivos
- Comprimir CVs antes de subir a OCI
- Reducir costos de almacenamiento

### 2. Cache de Procesamiento
- Cachear resultados de Gemini
- Evitar reprocesamiento innecesario

### 3. Análisis Avanzado
- Integración con más modelos de IA
- Análisis de sentimientos en CVs

### 4. Dashboard de Métricas
- Visualización de uso de almacenamiento
- Métricas de procesamiento en tiempo real

## 🎯 Beneficios del Sistema

### ✅ Ventajas
- **Escalabilidad**: OCI maneja millones de archivos
- **Seguridad**: PARs con expiración controlada
- **Costo-efectivo**: Solo pagas por lo que usas
- **Multi-tenant**: Aislamiento completo por tenant
- **IA Integrada**: Procesamiento automático
- **Alta Disponibilidad**: 99.9% SLA de OCI

### 📊 Comparación con Google Sheets
| Característica | OCI Object Storage | Google Sheets |
|----------------|-------------------|---------------|
| Capacidad | Ilimitada | 10M celdas |
| Seguridad | Enterprise-grade | Básica |
| Costo | Muy bajo | Gratuito limitado |
| Escalabilidad | Alta | Limitada |
| Integración IA | Nativa | Manual |
| Multi-tenant | Nativo | Complejo |

## 🔗 Enlaces Útiles

- [OCI Object Storage Documentation](https://docs.oracle.com/en-us/iaas/Content/Object/Concepts/objectstorageoverview.htm)
- [OCI Python SDK](https://docs.oracle.com/en-us/iaas/tools/python/latest/)
- [Gemini AI Documentation](https://ai.google.dev/docs)
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cli.htm)

---

**Nota**: Este sistema está diseñado para ser robusto, escalable y seguro. La implementación completa requiere configuración cuidadosa de OCI y pruebas exhaustivas en entorno de desarrollo antes del despliegue en producción.
