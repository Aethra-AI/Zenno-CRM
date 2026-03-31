import os
import requests
import json
import logging

# Configurar logger interno para depuración
logger = logging.getLogger("esc_crm")

class ESCCRMIntegration:
    def __init__(self):
        self.base_url = os.getenv('ESC_CRM_URL')
        self.api_key = os.getenv('ESC_TENANT_API_KEY')
        self.user_id = os.getenv('ESC_USER_ID')
        self.headers = {
            'X-API-Key': self.api_key,
            'X-ESC-User-ID': str(self.user_id) if self.user_id else '',
            'Content-Type': 'application/json'
        }

    def _call_api(self, method, endpoint, data=None, params=None):
        if not self.base_url or not self.api_key:
            return {"error": "Falta configuración de URL o API Key en el entorno."}

        url = f"{self.base_url.rstrip('/')}{endpoint}"
        try:
            response = requests.request(
                method=method, url=url, headers=self.headers,
                json=data, params=params, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Fallo en llamada al CRM: {str(e)}"}

    def get_vacancies(self, city=None, keyword=None, limit=10):
        params = {'limit': limit}
        if city: params['city'] = city
        if keyword: params['keyword'] = keyword
        return self._call_api('GET', '/api/public/vacancies', params=params)

    def search_candidates(self, query=None, limit=20):
        params = {'limit': limit}
        if query: params['q'] = query
        return self._call_api('GET', '/api/public/candidates/search', params=params)

    def get_candidate_details(self, candidate_id):
        # Convertir a int si viene como string
        try:
            cid = int(candidate_id)
        except:
            return {"error": "ID de candidato inválido"}
        return self._call_api('GET', f'/api/public/candidates/{cid}')

    def register_application(self, vacancy_id, candidate_data):
        payload = {"vacancy_id": vacancy_id, "candidate": candidate_data}
        return self._call_api('POST', '/api/public/applications', data=payload)

# Instancia global
_instance = ESCCRMIntegration()

# EXPORTACIÓN DE HERRAMIENTAS (Utilizadas por el motor de IA)

def get_vacancies(city: str = None, keyword: str = None, limit: int = 10):
    """
    Obtiene una lista de vacantes de empleo activas en el CRM.
    :param city: Ciudad para filtrar las vacantes (opcional).
    :param keyword: Palabra clave (cargo o requisito) para buscar (opcional).
    :param limit: Cantidad máxima de resultados a devolver (default 10).
    """
    return _instance.get_vacancies(city, keyword, limit)

def search_candidates(query: str = None, limit: int = 20):
    """
    Busca candidatos en la base de datos usando palabras clave (Keys).
    Funciona igual que la barra de búsqueda del CRM (Ej: 'SPS Mesero').
    :param query: Términos de búsqueda (nombre, id, ciudad, habilidades).
    :param limit: Cantidad máxima de resultados a devolver (default 20).
    """
    return _instance.search_candidates(query, limit)

def get_candidate_details(candidate_id: int):
    """
    Muestra el perfil detallado de un candidato específico del CRM.
    Útil para analizar experiencia y habilidades a profundidad.
    :param candidate_id: El ID único numérico del candidato.
    """
    return _instance.get_candidate_details(candidate_id)

def register_application(vacancy_id: int, candidate_data: dict):
    """
    Registra formalmente a un candidato en una vacante específica del CRM.
    :param vacancy_id: El ID de la vacante a la que aplica.
    :param candidate_data: Diccionario con {nombre, identidad, telefono}.
    """
    return _instance.register_application(vacancy_id, candidate_data)
