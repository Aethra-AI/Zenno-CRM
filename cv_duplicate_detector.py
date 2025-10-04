#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from difflib import SequenceMatcher
import phonenumbers
from email_validator import validate_email, EmailNotValidError
import mysql.connector
from dotenv import load_dotenv
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CVDuplicateDetector:
    """Detector de duplicados usando múltiples criterios"""
    
    def __init__(self):
        """Inicializar detector de duplicados"""
        load_dotenv()
        self.similarity_threshold = 0.85  # Umbral de similitud para considerar duplicado
        self.phone_similarity_threshold = 0.8  # Umbral para teléfonos
        self.name_similarity_threshold = 0.9  # Umbral para nombres
    
    def get_db_connection(self):
        """Obtener conexión a la base de datos"""
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'crm_henmir')
        )
    
    def normalize_phone(self, phone: str) -> str:
        """Normalizar número de teléfono para comparación"""
        if not phone:
            return ""
        
        # Remover caracteres no numéricos excepto +
        phone = re.sub(r'[^\d\+]', '', phone)
        
        # Agregar + si no está presente
        if not phone.startswith('+'):
            if len(phone) == 8:  # Número local
                phone = '+504' + phone
            elif len(phone) == 11 and phone.startswith('504'):
                phone = '+' + phone
        
        return phone
    
    def normalize_name(self, name: str) -> str:
        """Normalizar nombre para comparación"""
        if not name:
            return ""
        
        # Convertir a minúsculas y remover acentos
        name = name.lower()
        name = re.sub(r'[áàäâ]', 'a', name)
        name = re.sub(r'[éèëê]', 'e', name)
        name = re.sub(r'[íìïî]', 'i', name)
        name = re.sub(r'[óòöô]', 'o', name)
        name = re.sub(r'[úùüû]', 'u', name)
        name = re.sub(r'[ñ]', 'n', name)
        
        # Remover caracteres especiales
        name = re.sub(r'[^\w\s]', '', name)
        
        # Normalizar espacios
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcular similitud entre dos textos"""
        if not text1 or not text2:
            return 0.0
        
        return SequenceMatcher(None, text1, text2).ratio()
    
    def is_phone_similar(self, phone1: str, phone2: str) -> bool:
        """Verificar si dos teléfonos son similares"""
        if not phone1 or not phone2:
            return False
        
        norm_phone1 = self.normalize_phone(phone1)
        norm_phone2 = self.normalize_phone(phone2)
        
        if norm_phone1 == norm_phone2:
            return True
        
        # Comparar similitud
        similarity = self.calculate_similarity(norm_phone1, norm_phone2)
        return similarity >= self.phone_similarity_threshold
    
    def is_name_similar(self, name1: str, name2: str) -> bool:
        """Verificar si dos nombres son similares"""
        if not name1 or not name2:
            return False
        
        norm_name1 = self.normalize_name(name1)
        norm_name2 = self.normalize_name(name2)
        
        if norm_name1 == norm_name2:
            return True
        
        # Comparar similitud
        similarity = self.calculate_similarity(norm_name1, norm_name2)
        return similarity >= self.name_similarity_threshold
    
    def find_duplicates_by_email(self, email: str, tenant_id: int) -> List[Dict[str, Any]]:
        """Buscar duplicados por email"""
        if not email:
            return []
        
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT id_afiliado, nombre_completo, email, telefono, fecha_registro
                FROM Afiliados 
                WHERE email = %s AND tenant_id = %s
            """, (email, tenant_id))
            
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
    
    def find_duplicates_by_phone(self, phone: str, tenant_id: int) -> List[Dict[str, Any]]:
        """Buscar duplicados por teléfono"""
        if not phone:
            return []
        
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Buscar teléfonos exactos
            cursor.execute("""
                SELECT id_afiliado, nombre_completo, email, telefono, fecha_registro
                FROM Afiliados 
                WHERE telefono = %s AND tenant_id = %s
            """, (phone, tenant_id))
            
            exact_matches = cursor.fetchall()
            
            # Buscar teléfonos similares
            cursor.execute("""
                SELECT id_afiliado, nombre_completo, email, telefono, fecha_registro
                FROM Afiliados 
                WHERE telefono IS NOT NULL AND tenant_id = %s
            """, (tenant_id,))
            
            all_candidates = cursor.fetchall()
            similar_matches = []
            
            for candidate in all_candidates:
                if self.is_phone_similar(phone, candidate['telefono']):
                    similar_matches.append(candidate)
            
            return exact_matches + similar_matches
        finally:
            cursor.close()
            conn.close()
    
    def find_duplicates_by_name(self, name: str, tenant_id: int) -> List[Dict[str, Any]]:
        """Buscar duplicados por nombre"""
        if not name:
            return []
        
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Buscar nombres similares
            cursor.execute("""
                SELECT id_afiliado, nombre_completo, email, telefono, fecha_registro
                FROM Afiliados 
                WHERE nombre_completo IS NOT NULL AND tenant_id = %s
            """, (tenant_id,))
            
            all_candidates = cursor.fetchall()
            similar_matches = []
            
            for candidate in all_candidates:
                if self.is_name_similar(name, candidate['nombre_completo']):
                    similar_matches.append(candidate)
            
            return similar_matches
        finally:
            cursor.close()
            conn.close()
    
    def find_duplicates_comprehensive(self, candidate_data: Dict[str, Any], tenant_id: int) -> List[Dict[str, Any]]:
        """Buscar duplicados usando múltiples criterios"""
        duplicates = []
        
        # 1. Buscar por email (más confiable)
        if candidate_data.get('email'):
            email_duplicates = self.find_duplicates_by_email(candidate_data['email'], tenant_id)
            duplicates.extend(email_duplicates)
        
        # 2. Buscar por teléfono
        if candidate_data.get('telefono'):
            phone_duplicates = self.find_duplicates_by_phone(candidate_data['telefono'], tenant_id)
            duplicates.extend(phone_duplicates)
        
        # 3. Buscar por nombre (menos confiable, solo si no hay email ni teléfono)
        if not candidate_data.get('email') and not candidate_data.get('telefono'):
            if candidate_data.get('nombre_completo'):
                name_duplicates = self.find_duplicates_by_name(candidate_data['nombre_completo'], tenant_id)
                duplicates.extend(name_duplicates)
        
        # Eliminar duplicados
        unique_duplicates = []
        seen_ids = set()
        
        for duplicate in duplicates:
            if duplicate['id_afiliado'] not in seen_ids:
                unique_duplicates.append(duplicate)
                seen_ids.add(duplicate['id_afiliado'])
        
        return unique_duplicates
    
    def calculate_duplicate_confidence(self, candidate_data: Dict[str, Any], duplicate: Dict[str, Any]) -> float:
        """Calcular confianza de que es un duplicado"""
        confidence = 0.0
        
        # Email exacto (máxima confianza)
        if candidate_data.get('email') and duplicate.get('email'):
            if candidate_data['email'].lower() == duplicate['email'].lower():
                confidence += 0.5
        
        # Teléfono similar
        if candidate_data.get('telefono') and duplicate.get('telefono'):
            if self.is_phone_similar(candidate_data['telefono'], duplicate['telefono']):
                confidence += 0.3
        
        # Nombre similar
        if candidate_data.get('nombre_completo') and duplicate.get('nombre_completo'):
            if self.is_name_similar(candidate_data['nombre_completo'], duplicate['nombre_completo']):
                confidence += 0.2
        
        return min(confidence, 1.0)
    
    def classify_duplicate(self, candidate_data: Dict[str, Any], duplicate: Dict[str, Any]) -> str:
        """Clasificar tipo de duplicado"""
        confidence = self.calculate_duplicate_confidence(candidate_data, duplicate)
        
        if confidence >= 0.8:
            return 'high_confidence'
        elif confidence >= 0.5:
            return 'medium_confidence'
        else:
            return 'low_confidence'

# Función de utilidad
def create_duplicate_detector() -> CVDuplicateDetector:
    """Crear instancia del detector de duplicados"""
    return CVDuplicateDetector()

if __name__ == "__main__":
    # Prueba del detector
    detector = create_duplicate_detector()
    print("Detector de duplicados configurado correctamente")
