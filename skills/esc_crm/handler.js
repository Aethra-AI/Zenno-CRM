const axios = require('axios');

/**
 * SKILL: esc_crm
 * Esta skill permite interactuar directamente con la API de ESC CRM.
 */

async function callCrm(method, endpoint, data = null, params = null) {
  const baseUrl = process.env.ESC_CRM_URL || 'http://esc-backend:5000';
  const apiKey = process.env.ESC_TENANT_API_KEY;
  const userId = process.env.ESC_USER_ID;

  if (!baseUrl || !apiKey) {
    throw new Error("Falta configuración de CRM (URL o API Key) en el entorno.");
  }

  const url = baseUrl.replace(/\/$/, '') + endpoint;
  
  try {
    const response = await axios({
      method: method,
      url: url,
      headers: {
        'X-API-Key': apiKey,
        'X-ESC-User-ID': userId || '',
        'Content-Type': 'application/json'
      },
      data: data,
      params: params,
      timeout: 30000
    });
    return response.data;
  } catch (error) {
    const errorMsg = error.response ? JSON.stringify(error.response.data) : error.message;
    throw new Error(`Fallo en llamada al CRM: ${errorMsg}`);
  }
}

module.exports = {
  /**
   * Busca candidatos por palabras clave (Keys)
   * @param {string} query - Palabras clave (Ej: "SPS Mesero")
   * @param {number} limit - Máximo de resultados
   */
  async search_candidates({ query, limit = 20 }) {
    return await callCrm('GET', '/api/public/candidates/search', null, { q: query, limit });
  },

  /**
   * Obtiene detalles de un candidato
   * @param {number} candidate_id - ID del candidato
   */
  async get_candidate_details({ candidate_id }) {
    return await callCrm('GET', `/api/public/candidates/${candidate_id}`);
  },

  /**
   * Consulta vacantes activas
   */
  async get_vacancies({ city, keyword, limit = 10 }) {
    return await callCrm('GET', '/api/public/vacancies', null, { city, keyword, limit });
  },

  /**
   * Registra una postulación
   */
  async register_application({ vacancy_id, candidate_data }) {
    return await callCrm('POST', '/api/public/applications', { vacancy_id, candidate: candidate_data });
  }
};
