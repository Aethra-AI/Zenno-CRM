#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class CVConfig:
    """Configuración para el procesamiento de CVs"""
    
    # Configuración de archivos
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 10485760))  # 10MB
    ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', 'pdf,docx,doc,jpg,jpeg,png,gif,bmp').split(',')
    TEMP_UPLOAD_DIR = os.getenv('TEMP_UPLOAD_DIR', 'temp_uploads')
    TEMP_JOBS_DIR = os.getenv('TEMP_JOBS_DIR', 'temp_jobs')
    
    # Configuración de procesamiento
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 50))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 5))
    
    # Configuración de Gemini
    GEMINI_API_KEYS = [
        os.getenv('GEMINI_API_KEY_1'),
        os.getenv('GEMINI_API_KEY_2'),
        os.getenv('GEMINI_API_KEY_3'),
        os.getenv('GEMINI_API_KEY_4'),
        os.getenv('GEMINI_API_KEY_5')
    ]
    
    # Filtrar API keys válidas
    VALID_GEMINI_KEYS = [key for key in GEMINI_API_KEYS if key]
    
    # Configuración de base de datos
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'crm_henmir')
    }
    
    @classmethod
    def validate_config(cls):
        """Validar configuración"""
        errors = []
        
        if not cls.VALID_GEMINI_KEYS:
            errors.append("No se encontraron API keys válidas de Gemini")
        
        if cls.BATCH_SIZE <= 0:
            errors.append("BATCH_SIZE debe ser mayor a 0")
        
        if cls.MAX_WORKERS <= 0:
            errors.append("MAX_WORKERS debe ser mayor a 0")
        
        if cls.MAX_FILE_SIZE <= 0:
            errors.append("MAX_FILE_SIZE debe ser mayor a 0")
        
        if not cls.ALLOWED_EXTENSIONS:
            errors.append("ALLOWED_EXTENSIONS no puede estar vacío")
        
        return errors
    
    @classmethod
    def get_gemini_keys(cls):
        """Obtener API keys de Gemini válidas"""
        return cls.VALID_GEMINI_KEYS
    
    @classmethod
    def get_db_config(cls):
        """Obtener configuración de base de datos"""
        return cls.DB_CONFIG
    
    @classmethod
    def is_file_allowed(cls, filename):
        """Verificar si un archivo está permitido"""
        if not filename:
            return False
        
        extension = filename.lower().split('.')[-1]
        return extension in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def is_file_size_valid(cls, file_size):
        """Verificar si el tamaño del archivo es válido"""
        return file_size <= cls.MAX_FILE_SIZE

# Instancia global de configuración
config = CVConfig()

if __name__ == "__main__":
    # Validar configuración
    errors = config.validate_config()
    
    if errors:
        print("❌ Errores de configuración:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuración válida")
        print(f"  - API Keys de Gemini: {len(config.VALID_GEMINI_KEYS)}")
        print(f"  - Tamaño de lote: {config.BATCH_SIZE}")
        print(f"  - Workers máximos: {config.MAX_WORKERS}")
        print(f"  - Tamaño máximo de archivo: {config.MAX_FILE_SIZE / 1024 / 1024:.1f}MB")
        print(f"  - Extensiones permitidas: {', '.join(config.ALLOWED_EXTENSIONS)}")
