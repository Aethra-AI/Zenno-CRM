import os
import requests
import json

class ESCCRMIntegration:
    def __init__(self):
        self.base_url = os.getenv('ESC_CRM_URL')
        self.api_key = os.getenv('ESC_TENANT_API_KEY')
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }

    def _call_api(self, method, endpoint, data=None, params=None):
        if not self.base_url or not self.api_key:
            return {"error": "ESC CRM configuration missing (URL or API Key)"}
        
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"API call failed: {str(e)}"}

    def get_vacancies(self, city=None, keyword=None):
        """Obtiene vacantes activas del CRM filtradas por ciudad o palabra clave"""
        params = {}
        if city: params['city'] = city
        if keyword: params['keyword'] = keyword
        return self._call_api('GET', '/api/public/vacancies', params=params)

    def search_candidate(self, identity=None, name=None):
        """Busca un candidato por identidad o nombre"""
        params = {}
        if identity: params['identity'] = identity
        if name: params['name'] = name
        return self._call_api('GET', '/api/public/candidates', params=params)

    def register_application(self, vacancy_id, candidate_data):
        """Registra una nueva postulación en el CRM"""
        payload = {
            "vacancy_id": vacancy_id,
            "candidate": candidate_data  # Incluye nombre, identidad, telefono, etc.
        }
        return self._call_api('POST', '/api/public/applications', data=payload)

# Instancia para uso del agente
esc_crm = ESCCRMIntegration()
