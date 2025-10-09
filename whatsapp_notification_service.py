"""
📱 WHATSAPP NOTIFICATION SERVICE
=================================
Servicio centralizado para enviar notificaciones de WhatsApp según el modo configurado.

Modos soportados:
- WhatsApp API: Para conversaciones completas y notificaciones
- WhatsApp Web: SOLO para notificaciones automáticas (no gestiona conversaciones)
"""

import logging
import os
from typing import Dict, Optional, Tuple
from whatsapp_config_manager import get_tenant_whatsapp_config
from whatsapp_business_api_manager import WhatsAppBusinessAPIManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppNotificationService:
    """
    Servicio para enviar notificaciones de WhatsApp
    Determina automáticamente qué modo usar según la configuración del tenant
    """
    
    def __init__(self):
        self.api_manager = WhatsAppBusinessAPIManager()
    
    def get_active_mode(self, tenant_id: int) -> Optional[str]:
        """
        Obtiene el modo activo de WhatsApp para un tenant
        
        Returns:
            'business_api', 'whatsapp_web' o None si no hay configuración
        """
        try:
            config = get_tenant_whatsapp_config(tenant_id)
            if not config:
                logger.warning(f"⚠️ No hay configuración de WhatsApp para tenant {tenant_id}")
                return None
            
            # Si config es un dict con múltiples tipos, buscar el activo
            if isinstance(config, dict):
                for api_type, cfg in config.items():
                    if cfg and cfg.get('is_active'):
                        return api_type
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo modo activo tenant {tenant_id}: {str(e)}")
            return None
    
    def send_application_notification(self, tenant_id: int, phone: str, candidate_name: str, 
                                     vacancy_title: str, city: str, salary: str, requirements: str) -> Tuple[bool, str]:
        """
        Enviar notificación de postulación
        Funciona con: WhatsApp API y WhatsApp Web
        
        Args:
            tenant_id: ID del tenant
            phone: Teléfono del candidato
            candidate_name: Nombre del candidato
            vacancy_title: Cargo solicitado
            city: Ciudad
            salary: Salario
            requirements: Requisitos
        
        Returns:
            Tuple[success, message]
        """
        try:
            mode = self.get_active_mode(tenant_id)
            
            if not mode:
                logger.info(f"ℹ️ No hay WhatsApp configurado para tenant {tenant_id}")
                return False, "No hay configuración de WhatsApp activa"
            
            # Preparar mensaje
            first_name = candidate_name.split(' ')[0]
            message = (
                f"¡Hola {first_name}! Te saluda Henmir. 👋\n\n"
                f"Hemos considerado tu perfil para una nueva oportunidad laboral y te hemos postulado a la siguiente vacante:\n\n"
                f"📌 *Puesto:* {vacancy_title}\n"
                f"📍 *Ubicación:* {city}\n"
                f"💰 *Salario:* {salary}\n\n"
                f"*Requisitos principales:*\n{requirements}\n\n"
                "Por favor, confirma si estás interesado/a en continuar con este proceso. ¡Mucho éxito!"
            )
            
            return self._send_message(tenant_id, mode, phone, message, 'application')
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación de postulación: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def send_interview_notification(self, tenant_id: int, phone: str, candidate_name: str,
                                   vacancy_title: str, company: str, interview_date: str, 
                                   interviewer: str, notes: str = "") -> Tuple[bool, str]:
        """
        Enviar notificación de entrevista programada
        Funciona con: WhatsApp API y WhatsApp Web
        
        Args:
            tenant_id: ID del tenant
            phone: Teléfono del candidato
            candidate_name: Nombre del candidato
            vacancy_title: Cargo solicitado
            company: Empresa
            interview_date: Fecha formateada de la entrevista
            interviewer: Entrevistador
            notes: Notas adicionales
        
        Returns:
            Tuple[success, message]
        """
        try:
            mode = self.get_active_mode(tenant_id)
            
            if not mode:
                logger.info(f"ℹ️ No hay WhatsApp configurado para tenant {tenant_id}")
                return False, "No hay configuración de WhatsApp activa"
            
            # Preparar mensaje
            first_name = candidate_name.split(' ')[0]
            message = (
                f"¡Buenas noticias, {first_name}! 🎉\n\n"
                f"Hemos agendado tu entrevista para la vacante de *{vacancy_title}* en la empresa *{company}*.\n\n"
                f"🗓️ *Fecha y Hora:* {interview_date}\n"
                f"👤 *Entrevistador(a):* {interviewer}\n\n"
            )
            
            if notes:
                message += f"*Detalles adicionales:*\n{notes}\n\n"
            
            message += "Por favor, sé puntual. ¡Te deseamos mucho éxito en tu entrevista!"
            
            return self._send_message(tenant_id, mode, phone, message, 'interview')
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación de entrevista: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def send_hired_notification(self, tenant_id: int, phone: str, candidate_name: str,
                               vacancy_title: str, company: str) -> Tuple[bool, str]:
        """
        Enviar notificación de contratación
        Funciona con: WhatsApp API y WhatsApp Web
        
        Args:
            tenant_id: ID del tenant
            phone: Teléfono del candidato
            candidate_name: Nombre del candidato
            vacancy_title: Cargo solicitado
            company: Empresa
        
        Returns:
            Tuple[success, message]
        """
        try:
            mode = self.get_active_mode(tenant_id)
            
            if not mode:
                logger.info(f"ℹ️ No hay WhatsApp configurado para tenant {tenant_id}")
                return False, "No hay configuración de WhatsApp activa"
            
            # Preparar mensaje
            first_name = candidate_name.split(' ')[0]
            message = (
                f"¡FELICIDADES, {first_name}! 🥳\n\n"
                f"Nos complace enormemente informarte que has sido **CONTRATADO/A** para el puesto de *{vacancy_title}* en la empresa *{company}*.\n\n"
                "Este es un gran logro y el resultado de tu excelente desempeño en el proceso de selección. "
                "En breve, el equipo de recursos humanos de la empresa se pondrá en contacto contigo para coordinar los siguientes pasos.\n\n"
                "De parte de todo el equipo de Henmir, ¡te deseamos el mayor de los éxitos en tu nuevo rol!"
            )
            
            return self._send_message(tenant_id, mode, phone, message, 'hired')
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación de contratación: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def send_status_change_notification(self, tenant_id: int, phone: str, candidate_name: str,
                                       vacancy_title: str, new_status: str) -> Tuple[bool, str]:
        """
        Enviar notificación de cambio de estado
        Funciona con: WhatsApp API y WhatsApp Web
        
        Args:
            tenant_id: ID del tenant
            phone: Teléfono del candidato
            candidate_name: Nombre del candidato
            vacancy_title: Cargo solicitado
            new_status: Nuevo estado
        
        Returns:
            Tuple[success, message]
        """
        try:
            mode = self.get_active_mode(tenant_id)
            
            if not mode:
                logger.info(f"ℹ️ No hay WhatsApp configurado para tenant {tenant_id}")
                return False, "No hay configuración de WhatsApp activa"
            
            # Preparar mensaje según el estado
            first_name = candidate_name.split(' ')[0]
            
            status_messages = {
                'En Revisión': f"Hola {first_name}, tu postulación para {vacancy_title} está siendo revisada por nuestro equipo. Te mantendremos informado.",
                'Preseleccionado': f"¡Buenas noticias {first_name}! Has sido preseleccionado para {vacancy_title}. Pronto te contactaremos.",
                'Rechazado': f"Hola {first_name}, lamentamos informarte que en esta ocasión no continuarás en el proceso para {vacancy_title}. Te invitamos a postularte a otras oportunidades."
            }
            
            message = status_messages.get(new_status, 
                f"Hola {first_name}, el estado de tu postulación para {vacancy_title} ha sido actualizado a: {new_status}")
            
            return self._send_message(tenant_id, mode, phone, message, 'status_change')
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación de cambio de estado: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def send_bot_campaign_message(self, tenant_id: int, phone: str, message: str) -> Tuple[bool, str]:
        """
        Enviar mensaje de campaña preparado por el bot
        Funciona con: WhatsApp API y WhatsApp Web
        
        Args:
            tenant_id: ID del tenant
            phone: Teléfono destino
            message: Mensaje preparado
        
        Returns:
            Tuple[success, message]
        """
        try:
            mode = self.get_active_mode(tenant_id)
            
            if not mode:
                logger.info(f"ℹ️ No hay WhatsApp configurado para tenant {tenant_id}")
                return False, "No hay configuración de WhatsApp activa"
            
            return self._send_message(tenant_id, mode, phone, message, 'campaign')
            
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje de campaña: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def _send_message(self, tenant_id: int, mode: str, phone: str, message: str, 
                     notification_type: str) -> Tuple[bool, str]:
        """
        Enviar mensaje usando el modo configurado
        
        Args:
            tenant_id: ID del tenant
            mode: 'business_api' o 'whatsapp_web'
            phone: Teléfono destino
            message: Mensaje a enviar
            notification_type: Tipo de notificación
        
        Returns:
            Tuple[success, message]
        """
        try:
            if mode == 'business_api':
                # Usar WhatsApp Business API
                result = self.api_manager.send_text_message(tenant_id, phone, message)
                
                if result.get('status') == 'success':
                    logger.info(f"✅ Mensaje enviado via API - Tipo: {notification_type} - Teléfono: {phone}")
                    return True, "Mensaje enviado exitosamente via WhatsApp API"
                else:
                    error = result.get('error', 'Error desconocido')
                    logger.error(f"❌ Error enviando via API: {error}")
                    return False, f"Error: {error}"
            
            elif mode == 'whatsapp_web':
                # Usar WhatsApp Web solo para notificaciones
                # Importar dinámicamente para evitar dependencias circulares
                from whatsapp_web_manager import send_notification_web
                
                success = send_notification_web(tenant_id, phone, message)
                
                if success:
                    logger.info(f"✅ Notificación enviada via Web - Tipo: {notification_type} - Teléfono: {phone}")
                    return True, "Notificación enviada exitosamente via WhatsApp Web"
                else:
                    logger.error(f"❌ Error enviando via Web")
                    return False, "Error enviando notificación via WhatsApp Web"
            
            else:
                logger.error(f"❌ Modo desconocido: {mode}")
                return False, f"Modo de WhatsApp desconocido: {mode}"
                
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje: {str(e)}")
            return False, f"Error enviando mensaje: {str(e)}"
    
    def can_use_for_conversations(self, tenant_id: int) -> bool:
        """
        Verifica si el tenant puede usar WhatsApp para conversaciones
        Solo WhatsApp API soporta conversaciones completas
        
        Args:
            tenant_id: ID del tenant
        
        Returns:
            True si puede gestionar conversaciones, False si no
        """
        try:
            mode = self.get_active_mode(tenant_id)
            
            # Solo WhatsApp API soporta conversaciones
            return mode == 'business_api'
            
        except Exception as e:
            logger.error(f"❌ Error verificando capacidad de conversaciones: {str(e)}")
            return False


# =====================================================
# INSTANCIA GLOBAL
# =====================================================

# Instancia global del servicio de notificaciones
notification_service = WhatsAppNotificationService()


# =====================================================
# FUNCIONES DE UTILIDAD
# =====================================================

def send_application_notification(tenant_id: int, phone: str, candidate_name: str, 
                                 vacancy_title: str, city: str, salary: str, requirements: str) -> Tuple[bool, str]:
    """
    Enviar notificación de postulación
    """
    return notification_service.send_application_notification(
        tenant_id, phone, candidate_name, vacancy_title, city, salary, requirements
    )

def send_interview_notification(tenant_id: int, phone: str, candidate_name: str,
                               vacancy_title: str, company: str, interview_date: str, 
                               interviewer: str, notes: str = "") -> Tuple[bool, str]:
    """
    Enviar notificación de entrevista
    """
    return notification_service.send_interview_notification(
        tenant_id, phone, candidate_name, vacancy_title, company, interview_date, interviewer, notes
    )

def send_hired_notification(tenant_id: int, phone: str, candidate_name: str,
                           vacancy_title: str, company: str) -> Tuple[bool, str]:
    """
    Enviar notificación de contratación
    """
    return notification_service.send_hired_notification(
        tenant_id, phone, candidate_name, vacancy_title, company
    )

def send_status_change_notification(tenant_id: int, phone: str, candidate_name: str,
                                   vacancy_title: str, new_status: str) -> Tuple[bool, str]:
    """
    Enviar notificación de cambio de estado
    """
    return notification_service.send_status_change_notification(
        tenant_id, phone, candidate_name, vacancy_title, new_status
    )

def send_bot_campaign_message(tenant_id: int, phone: str, message: str) -> Tuple[bool, str]:
    """
    Enviar mensaje de campaña
    """
    return notification_service.send_bot_campaign_message(tenant_id, phone, message)

def can_use_whatsapp_conversations(tenant_id: int) -> bool:
    """
    Verificar si el tenant puede usar WhatsApp para conversaciones
    Solo retorna True si está configurado con WhatsApp API
    """
    return notification_service.can_use_for_conversations(tenant_id)


# =====================================================
# EJEMPLO DE USO
# =====================================================

if __name__ == "__main__":
    # Ejemplo de uso
    service = WhatsAppNotificationService()
    
    # Verificar modo activo
    mode = service.get_active_mode(1)
    print(f"Modo activo para tenant 1: {mode}")
    
    # Verificar si puede usar conversaciones
    can_chat = service.can_use_for_conversations(1)
    print(f"¿Puede usar conversaciones?: {can_chat}")
    
    # Enviar notificación de postulación
    success, message = service.send_application_notification(
        tenant_id=1,
        phone="50412345678",
        candidate_name="Juan Pérez",
        vacancy_title="Desarrollador Python",
        city="Tegucigalpa",
        salary="L. 25,000",
        requirements="2 años de experiencia en Python y Flask"
    )
    
    print(f"Notificación enviada: {success} - {message}")
