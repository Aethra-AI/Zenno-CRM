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

class CVValidator:
    """Validador y limpiador de datos de candidatos"""
    
    def __init__(self):
        """Inicializar validador"""
        self.required_fields = ['nombre_completo', 'email']
        self.optional_fields = [
            'telefono', 'ciudad', 'cargo_solicitado', 'experiencia',
            'habilidades', 'grado_academico', 'fecha_nacimiento',
            'nacionalidad', 'linkedin', 'portfolio', 'skills', 'comentarios'
        ]
    
    def validate_candidate_data(self, candidate_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validar datos del candidato"""
        errors = []
        
        # Validar campos requeridos
        for field in self.required_fields:
            if not candidate_data.get(field):
                errors.append(f"Campo requerido faltante: {field}")
        
        # Validar email
        if candidate_data.get('email'):
            email_valid, email_error = self._validate_email(candidate_data['email'])
            if not email_valid:
                errors.append(f"Email inválido: {email_error}")
        
        # Validar teléfono
        if candidate_data.get('telefono'):
            phone_valid, phone_error = self._validate_phone(candidate_data['telefono'])
            if not phone_valid:
                errors.append(f"Teléfono inválido: {phone_error}")
        
        # Validar fecha de nacimiento
        if candidate_data.get('fecha_nacimiento'):
            date_valid, date_error = self._validate_date(candidate_data['fecha_nacimiento'])
            if not date_valid:
                errors.append(f"Fecha de nacimiento inválida: {date_error}")
        
        # Validar LinkedIn
        if candidate_data.get('linkedin'):
            linkedin_valid, linkedin_error = self._validate_linkedin(candidate_data['linkedin'])
            if not linkedin_valid:
                errors.append(f"LinkedIn inválido: {linkedin_error}")
        
        # Validar portfolio
        if candidate_data.get('portfolio'):
            portfolio_valid, portfolio_error = self._validate_portfolio(candidate_data['portfolio'])
            if not portfolio_valid:
                errors.append(f"Portfolio inválido: {portfolio_error}")
        
        return len(errors) == 0, errors
    
    def clean_candidate_data(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Limpiar y normalizar datos del candidato"""
        cleaned_data = {}
        
        # Limpiar nombre completo
        if candidate_data.get('nombre_completo'):
            cleaned_data['nombre_completo'] = self._clean_name(candidate_data['nombre_completo'])
        
        # Limpiar email
        if candidate_data.get('email'):
            cleaned_data['email'] = self._clean_email(candidate_data['email'])
        
        # Limpiar teléfono
        if candidate_data.get('telefono'):
            cleaned_data['telefono'] = self._clean_phone(candidate_data['telefono'])
        
        # Limpiar ciudad
        if candidate_data.get('ciudad'):
            cleaned_data['ciudad'] = self._clean_city(candidate_data['ciudad'])
        
        # Limpiar cargo solicitado
        if candidate_data.get('cargo_solicitado'):
            cleaned_data['cargo_solicitado'] = self._clean_job_title(candidate_data['cargo_solicitado'])
        
        # Limpiar experiencia
        if candidate_data.get('experiencia'):
            cleaned_data['experiencia'] = self._clean_experience(candidate_data['experiencia'])
        
        # Limpiar habilidades
        if candidate_data.get('habilidades'):
            cleaned_data['habilidades'] = self._clean_skills(candidate_data['habilidades'])
        
        # Limpiar grado académico
        if candidate_data.get('grado_academico'):
            cleaned_data['grado_academico'] = self._clean_education(candidate_data['grado_academico'])
        
        # Limpiar fecha de nacimiento
        if candidate_data.get('fecha_nacimiento'):
            cleaned_data['fecha_nacimiento'] = self._clean_date(candidate_data['fecha_nacimiento'])
        
        # Limpiar nacionalidad
        if candidate_data.get('nacionalidad'):
            cleaned_data['nacionalidad'] = self._clean_nationality(candidate_data['nacionalidad'])
        
        # Limpiar LinkedIn
        if candidate_data.get('linkedin'):
            cleaned_data['linkedin'] = self._clean_linkedin(candidate_data['linkedin'])
        
        # Limpiar portfolio
        if candidate_data.get('portfolio'):
            cleaned_data['portfolio'] = self._clean_portfolio(candidate_data['portfolio'])
        
        # Limpiar skills
        if candidate_data.get('skills'):
            cleaned_data['skills'] = self._clean_skills(candidate_data['skills'])
        
        # Limpiar comentarios
        if candidate_data.get('comentarios'):
            cleaned_data['comentarios'] = self._clean_comments(candidate_data['comentarios'])
        
        return cleaned_data
    
    def _validate_email(self, email: str) -> Tuple[bool, str]:
        """Validar email"""
        try:
            validate_email(email)
            return True, ""
        except EmailNotValidError as e:
            return False, str(e)
    
    def _validate_phone(self, phone: str) -> Tuple[bool, str]:
        """Validar teléfono"""
        try:
            # Intentar parsear con phonenumbers
            parsed = phonenumbers.parse(phone, None)
            if phonenumbers.is_valid_number(parsed):
                return True, ""
            else:
                return False, "Número de teléfono inválido"
        except:
            # Si falla, usar validación básica
            if re.match(r'^[\+]?[0-9\s\-\(\)]{7,20}$', phone):
                return True, ""
            else:
                return False, "Formato de teléfono inválido"
    
    def _validate_date(self, date_str: str) -> Tuple[bool, str]:
        """Validar fecha de nacimiento"""
        try:
            # Intentar parsear fecha
            datetime.strptime(date_str, '%Y-%m-%d')
            
            # Verificar que no sea futura
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            if date_obj > datetime.now():
                return False, "Fecha de nacimiento no puede ser futura"
            
            # Verificar que no sea muy antigua (más de 100 años)
            if (datetime.now() - date_obj).days > 36500:
                return False, "Fecha de nacimiento muy antigua"
            
            return True, ""
        except ValueError:
            return False, "Formato de fecha inválido (YYYY-MM-DD)"
    
    def _validate_linkedin(self, linkedin: str) -> Tuple[bool, str]:
        """Validar LinkedIn"""
        linkedin_pattern = r'^https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9\-]+/?$'
        if re.match(linkedin_pattern, linkedin):
            return True, ""
        else:
            return False, "URL de LinkedIn inválida"
    
    def _validate_portfolio(self, portfolio: str) -> Tuple[bool, str]:
        """Validar portfolio"""
        portfolio_pattern = r'^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$'
        if re.match(portfolio_pattern, portfolio):
            return True, ""
        else:
            return False, "URL de portfolio inválida"
    
    def _clean_name(self, name: str) -> str:
        """Limpiar nombre completo"""
        # Remover caracteres especiales excepto espacios y guiones
        name = re.sub(r'[^\w\s\-]', '', name)
        # Normalizar espacios
        name = re.sub(r'\s+', ' ', name)
        # Capitalizar palabras
        name = ' '.join(word.capitalize() for word in name.split())
        return name.strip()
    
    def _clean_email(self, email: str) -> str:
        """Limpiar email"""
        return email.lower().strip()
    
    def _clean_phone(self, phone: str) -> str:
        """Limpiar teléfono"""
        # Remover caracteres no numéricos excepto + al inicio
        phone = re.sub(r'[^\d\+]', '', phone)
        
        # Agregar + si no está presente y no empieza con código de país
        if not phone.startswith('+'):
            # Asumir código de país de Honduras si no está presente
            if len(phone) == 8:
                phone = '+504' + phone
            elif len(phone) == 11 and phone.startswith('504'):
                phone = '+' + phone
        
        return phone
    
    def _clean_city(self, city: str) -> str:
        """Limpiar ciudad"""
        city = re.sub(r'[^\w\s]', '', city)
        city = re.sub(r'\s+', ' ', city)
        return city.strip().title()
    
    def _clean_job_title(self, job_title: str) -> str:
        """Limpiar cargo solicitado"""
        job_title = re.sub(r'[^\w\s]', '', job_title)
        job_title = re.sub(r'\s+', ' ', job_title)
        return job_title.strip().title()
    
    def _clean_experience(self, experience: str) -> str:
        """Limpiar experiencia"""
        # Limpiar texto pero mantener estructura
        experience = re.sub(r'\s+', ' ', experience)
        return experience.strip()
    
    def _clean_skills(self, skills: str) -> str:
        """Limpiar habilidades"""
        # Convertir a lista y limpiar cada skill
        skills_list = [skill.strip() for skill in skills.split(',')]
        skills_list = [skill for skill in skills_list if skill]
        return ', '.join(skills_list)
    
    def _clean_education(self, education: str) -> str:
        """Limpiar grado académico"""
        education = re.sub(r'\s+', ' ', education)
        return education.strip()
    
    def _clean_date(self, date_str: str) -> str:
        """Limpiar fecha de nacimiento"""
        try:
            # Intentar parsear y reformatear
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%Y-%m-%d')
        except:
            return date_str
    
    def _clean_nationality(self, nationality: str) -> str:
        """Limpiar nacionalidad"""
        nationality = re.sub(r'[^\w\s]', '', nationality)
        nationality = re.sub(r'\s+', ' ', nationality)
        return nationality.strip().title()
    
    def _clean_linkedin(self, linkedin: str) -> str:
        """Limpiar LinkedIn"""
        if not linkedin.startswith('http'):
            linkedin = 'https://' + linkedin
        return linkedin.strip()
    
    def _clean_portfolio(self, portfolio: str) -> str:
        """Limpiar portfolio"""
        if not portfolio.startswith('http'):
            portfolio = 'https://' + portfolio
        return portfolio.strip()
    
    def _clean_comments(self, comments: str) -> str:
        """Limpiar comentarios"""
        comments = re.sub(r'\s+', ' ', comments)
        return comments.strip()
    
    def validate_batch(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validar lote de candidatos"""
        validated_candidates = []
        
        for candidate in candidates:
            # Limpiar datos
            cleaned_candidate = self.clean_candidate_data(candidate)
            
            # Validar datos
            is_valid, errors = self.validate_candidate_data(cleaned_candidate)
            
            if is_valid:
                validated_candidates.append({
                    'candidate': cleaned_candidate,
                    'status': 'valid',
                    'errors': []
                })
            else:
                validated_candidates.append({
                    'candidate': cleaned_candidate,
                    'status': 'invalid',
                    'errors': errors
                })
        
        return validated_candidates

# Función de utilidad
def create_cv_validator() -> CVValidator:
    """Crear instancia del validador"""
    return CVValidator()

if __name__ == "__main__":
    # Prueba del validador
    validator = create_cv_validator()
    print("Validador de CVs configurado correctamente")
