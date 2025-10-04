#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import phonenumbers
from email_validator import validate_email, EmailNotValidError

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CVDataCompleter:
    """Completador de datos faltantes en CVs"""
    
    def __init__(self):
        """Inicializar completador de datos"""
        self.required_fields = ['nombre_completo', 'email']
        self.optional_fields = [
            'telefono', 'ciudad', 'cargo_solicitado', 'experiencia',
            'habilidades', 'grado_academico', 'fecha_nacimiento',
            'nacionalidad', 'linkedin', 'portfolio', 'skills', 'comentarios'
        ]
    
    def extract_email_from_text(self, text: str) -> Optional[str]:
        """Extraer email del texto del CV"""
        if not text:
            return None
        
        # Patrón para emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        if emails:
            # Validar email
            try:
                validate_email(emails[0])
                return emails[0].lower()
            except EmailNotValidError:
                pass
        
        return None
    
    def extract_phone_from_text(self, text: str) -> Optional[str]:
        """Extraer teléfono del texto del CV"""
        if not text:
            return None
        
        # Patrones para teléfonos
        phone_patterns = [
            r'\+?504\s?\d{4}\s?\d{4}',  # Honduras: +504 1234 5678
            r'\+?1\s?\d{3}\s?\d{3}\s?\d{4}',  # US: +1 123 456 7890
            r'\+?52\s?\d{2}\s?\d{4}\s?\d{4}',  # México: +52 12 3456 7890
            r'\+?34\s?\d{3}\s?\d{3}\s?\d{3}',  # España: +34 123 456 789
            r'\+?\d{1,3}\s?\d{3,4}\s?\d{3,4}\s?\d{3,4}',  # Genérico
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                # Limpiar y normalizar
                phone = re.sub(r'[^\d\+]', '', phones[0])
                if len(phone) >= 8:  # Mínimo 8 dígitos
                    return phone
        
        return None
    
    def extract_name_from_text(self, text: str) -> Optional[str]:
        """Extraer nombre del texto del CV"""
        if not text:
            return None
        
        # Buscar patrones de nombre al inicio del texto
        lines = text.split('\n')[:10]  # Primeras 10 líneas
        
        for line in lines:
            line = line.strip()
            if len(line) < 3:
                continue
            
            # Patrón para nombres (2-3 palabras, solo letras)
            name_pattern = r'^[A-Za-záéíóúñÁÉÍÓÚÑ\s]{2,50}$'
            if re.match(name_pattern, line):
                # Verificar que no sea una palabra común
                common_words = [
                    'curriculum', 'vitae', 'cv', 'resume', 'perfil', 'profesional',
                    'desarrollador', 'programador', 'ingeniero', 'licenciado'
                ]
                
                if not any(word in line.lower() for word in common_words):
                    return line.title()
        
        return None
    
    def extract_city_from_text(self, text: str) -> Optional[str]:
        """Extraer ciudad del texto del CV"""
        if not text:
            return None
        
        # Ciudades comunes en Honduras
        honduras_cities = [
            'tegucigalpa', 'san pedro sula', 'la ceiba', 'choluteca', 'comayagua',
            'puerto cortes', 'el progreso', 'juticalpa', 'danli', 'santa rosa de copan'
        ]
        
        text_lower = text.lower()
        for city in honduras_cities:
            if city in text_lower:
                return city.title()
        
        # Buscar patrones de ubicación
        location_patterns = [
            r'ubicación[:\s]+([A-Za-z\s]+)',
            r'ciudad[:\s]+([A-Za-z\s]+)',
            r'residencia[:\s]+([A-Za-z\s]+)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text_lower)
            if match:
                city = match.group(1).strip()
                if len(city) > 2:
                    return city.title()
        
        return None
    
    def extract_job_title_from_text(self, text: str) -> Optional[str]:
        """Extraer cargo solicitado del texto del CV"""
        if not text:
            return None
        
        # Buscar en secciones específicas
        sections = ['objetivo', 'objetivo profesional', 'perfil', 'resumen']
        
        for section in sections:
            pattern = f'{section}[:\\s]+([A-Za-z\\s]+)'
            match = re.search(pattern, text.lower())
            if match:
                job_title = match.group(1).strip()
                if len(job_title) > 5:
                    return job_title.title()
        
        # Buscar en las primeras líneas
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            if len(line) > 10 and len(line) < 100:
                # Verificar si contiene palabras relacionadas con trabajo
                job_keywords = [
                    'desarrollador', 'programador', 'ingeniero', 'analista',
                    'consultor', 'gerente', 'director', 'coordinador',
                    'especialista', 'técnico', 'diseñador', 'arquitecto'
                ]
                
                if any(keyword in line.lower() for keyword in job_keywords):
                    return line.title()
        
        return None
    
    def extract_skills_from_text(self, text: str) -> Optional[str]:
        """Extraer habilidades del texto del CV"""
        if not text:
            return None
        
        # Buscar sección de habilidades
        skills_sections = ['habilidades', 'skills', 'tecnologías', 'herramientas', 'competencias']
        
        for section in skills_sections:
            pattern = f'{section}[:\\s]+([A-Za-z0-9\\s,.-]+)'
            match = re.search(pattern, text.lower())
            if match:
                skills = match.group(1).strip()
                if len(skills) > 5:
                    return skills
        
        # Buscar tecnologías comunes
        common_skills = [
            'javascript', 'python', 'java', 'react', 'angular', 'vue',
            'node.js', 'php', 'mysql', 'postgresql', 'mongodb',
            'html', 'css', 'bootstrap', 'git', 'docker', 'aws'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        if found_skills:
            return ', '.join(found_skills)
        
        return None
    
    def complete_missing_data(self, candidate_data: Dict[str, Any], cv_text: str) -> Dict[str, Any]:
        """Completar datos faltantes usando el texto del CV"""
        completed_data = candidate_data.copy()
        
        # Completar email si falta
        if not completed_data.get('email'):
            email = self.extract_email_from_text(cv_text)
            if email:
                completed_data['email'] = email
                logger.info(f"Email extraído del texto: {email}")
        
        # Completar teléfono si falta
        if not completed_data.get('telefono'):
            phone = self.extract_phone_from_text(cv_text)
            if phone:
                completed_data['telefono'] = phone
                logger.info(f"Teléfono extraído del texto: {phone}")
        
        # Completar nombre si falta
        if not completed_data.get('nombre_completo'):
            name = self.extract_name_from_text(cv_text)
            if name:
                completed_data['nombre_completo'] = name
                logger.info(f"Nombre extraído del texto: {name}")
        
        # Completar ciudad si falta
        if not completed_data.get('ciudad'):
            city = self.extract_city_from_text(cv_text)
            if city:
                completed_data['ciudad'] = city
                logger.info(f"Ciudad extraída del texto: {city}")
        
        # Completar cargo si falta
        if not completed_data.get('cargo_solicitado'):
            job_title = self.extract_job_title_from_text(cv_text)
            if job_title:
                completed_data['cargo_solicitado'] = job_title
                logger.info(f"Cargo extraído del texto: {job_title}")
        
        # Completar habilidades si falta
        if not completed_data.get('habilidades'):
            skills = self.extract_skills_from_text(cv_text)
            if skills:
                completed_data['habilidades'] = skills
                logger.info(f"Habilidades extraídas del texto: {skills}")
        
        return completed_data
    
    def validate_completed_data(self, candidate_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validar datos completados"""
        errors = []
        
        # Verificar campos requeridos
        for field in self.required_fields:
            if not candidate_data.get(field):
                errors.append(f"Campo requerido faltante: {field}")
        
        # Validar email si existe
        if candidate_data.get('email'):
            try:
                validate_email(candidate_data['email'])
            except EmailNotValidError:
                errors.append("Email inválido")
        
        # Validar teléfono si existe
        if candidate_data.get('telefono'):
            try:
                parsed_phone = phonenumbers.parse(candidate_data['telefono'], None)
                if not phonenumbers.is_valid_number(parsed_phone):
                    errors.append("Teléfono inválido")
            except:
                # Si falla la validación con phonenumbers, usar validación básica
                if not re.match(r'^[\+]?[0-9\s\-\(\)]{7,20}$', candidate_data['telefono']):
                    errors.append("Formato de teléfono inválido")
        
        return len(errors) == 0, errors
    
    def generate_missing_data_report(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generar reporte de datos faltantes"""
        missing_fields = []
        present_fields = []
        
        for field in self.required_fields + self.optional_fields:
            if candidate_data.get(field):
                present_fields.append(field)
            else:
                missing_fields.append(field)
        
        return {
            'total_fields': len(self.required_fields + self.optional_fields),
            'present_fields': len(present_fields),
            'missing_fields': len(missing_fields),
            'missing_list': missing_fields,
            'completion_percentage': (len(present_fields) / len(self.required_fields + self.optional_fields)) * 100
        }

# Función de utilidad
def create_data_completer() -> CVDataCompleter:
    """Crear instancia del completador de datos"""
    return CVDataCompleter()

if __name__ == "__main__":
    # Prueba del completador
    completer = create_data_completer()
    print("Completador de datos configurado correctamente")
