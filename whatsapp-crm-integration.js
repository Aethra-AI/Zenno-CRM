// ========================================
// INTEGRACIÓN DE API EN TU AGENTE DE WHATSAPP
// ========================================

/**
 * Configuración de la API
 * Como el agente está en la misma VM, usa localhost
 */
const WHATSAPP_API_CONFIG = {
    baseUrl: 'http://localhost:5000',  // Mismo servidor
    apiKey: 'TU_API_KEY_AQUI',  // Pon la API Key que generaste
    
    // Opcional: Si el backend usa otro puerto
    // baseUrl: 'http://localhost:OTRO_PUERTO',
};

/**
 * Función auxiliar para hacer requests a la API
 */
async function callCrmApi(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = `${WHATSAPP_API_CONFIG.baseUrl}${endpoint}${queryString ? '?' + queryString : ''}`;
    
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'X-API-Key': WHATSAPP_API_CONFIG.apiKey,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
        
    } catch (error) {
        console.error(`❌ Error llamando a ${endpoint}:`, error.message);
        throw error;
    }
}

// ========================================
// FUNCIONES PARA TU AGENTE
// ========================================

/**
 * 1. Buscar vacantes disponibles
 * Uso: Cuando el usuario pregunta por trabajos
 */
async function buscarVacantes(ciudad = null, limit = 5) {
    const params = { limit };
    if (ciudad) params.ciudad = ciudad;
    
    const data = await callCrmApi('/public-api/v1/vacancies', params);
    
    if (data.success && data.data.length > 0) {
        return {
            encontradas: true,
            vacantes: data.data,
            total: data.data.length
        };
    }
    
    return {
        encontradas: false,
        vacantes: [],
        total: 0
    };
}

/**
 * 2. Validar si un candidato está registrado
 * Uso: Cuando el usuario envía su número de identidad
 */
async function validarCandidato(identidad = null, nombre = null) {
    if (!identidad && !nombre) {
        throw new Error('Debes proporcionar identidad o nombre');
    }
    
    const params = {};
    if (identidad) params.identity = identidad.replace(/[-\s]/g, ''); // Limpiar guiones
    if (nombre) params.name = nombre;
    
    const data = await callCrmApi('/public-api/v1/candidates/validate', params);
    
    return {
        existe: data.exists,
        candidato: data.candidate || null,
        mensaje: data.message || null
    };
}

/**
 * 3. Buscar candidatos por nombre
 * Uso: Para búsquedas internas o verificaciones
 */
async function buscarCandidatos(termino, limit = 10) {
    const data = await callCrmApi('/public-api/v1/candidates/search', {
        q: termino,
        limit
    });
    
    if (data.success && data.total > 0) {
        return {
            encontrados: true,
            candidatos: data.data,
            total: data.total
        };
    }
    
    return {
        encontrados: false,
        candidatos: [],
        total: 0
    };
}

// ========================================
// EJEMPLOS DE USO EN TU BOT
// ========================================

/**
 * Ejemplo 1: Usuario pregunta por vacantes
 */
async function manejarSolicitudVacantes(mensaje, ciudad = null) {
    try {
        const resultado = await buscarVacantes(ciudad, 5);
        
        if (resultado.encontradas) {
            let respuesta = ciudad 
                ? `Tenemos ${resultado.total} vacantes en ${ciudad}:\n\n`
                : `Tenemos ${resultado.total} vacantes disponibles:\n\n`;
            
            resultado.vacantes.forEach((v, i) => {
                respuesta += `${i + 1}. *${v.cargo_solicitado}*\n`;
                respuesta += `   📍 ${v.ciudad}\n`;
                if (v.salario_rango) {
                    respuesta += `   💰 ${v.salario_rango}\n`;
                }
                respuesta += `   📝 ${v.descripcion?.substring(0, 100) || 'Ver detalles'}...\n\n`;
            });
            
            respuesta += '¿Te interesa alguna? Dime el número 👆';
            return respuesta;
        } else {
            return ciudad
                ? `No tengo vacantes disponibles en ${ciudad} ahora mismo. ¿Te interesa otra ciudad?`
                : 'No tenemos vacantes disponibles en este momento. ¿Quieres que te avise cuando haya nuevas?';
        }
        
    } catch (error) {
        console.error('Error buscando vacantes:', error);
        return 'Disculpa, hubo un error consultando las vacantes. Intenta de nuevo en un momento.';
    }
}

/**
 * Ejemplo 2: Usuario envía su identidad para validar registro
 */
async function manejarValidacionCandidato(identidad) {
    try {
        const resultado = await validarCandidato(identidad);
        
        if (resultado.existe) {
            const nombre = resultado.candidato.nombre_completo;
            return `¡Hola ${nombre}! 👋\n\nYa estás registrado en nuestro sistema.\n\n¿En qué puedo ayudarte?\n1. Ver vacantes disponibles\n2. Actualizar mi información\n3. Ver mis postulaciones`;
        } else {
            return `No encontré tu registro en el sistema. 🤔\n\n¿Quieres registrarte ahora? Solo necesito:\n• Tu nombre completo\n• Teléfono\n• Ciudad\n• Cargo que buscas`;
        }
        
    } catch (error) {
        console.error('Error validando candidato:', error);
        return 'Disculpa, hubo un error verificando tu registro. Intenta de nuevo.';
    }
}

/**
 * Ejemplo 3: Flujo completo de conversación
 */
async function manejarMensajeWhatsApp(mensaje, numeroTelefono) {
    const mensajeLower = mensaje.toLowerCase();
    
    // Detectar intención del usuario
    if (mensajeLower.includes('vacante') || mensajeLower.includes('trabajo')) {
        // Intentar detectar ciudad en el mensaje
        const ciudades = ['tegucigalpa', 'san pedro sula', 'choloma', 'la ceiba'];
        const ciudadMencionada = ciudades.find(c => mensajeLower.includes(c));
        
        return await manejarSolicitudVacantes(mensaje, ciudadMencionada);
    }
    
    // Detectar si está enviando identidad
    const identidadMatch = mensaje.match(/\d{4}[-\s]?\d{4}[-\s]?\d{5}/);
    if (identidadMatch) {
        return await manejarValidacionCandidato(identidadMatch[0]);
    }
    
    // Mensaje de bienvenida
    return `¡Hola! 👋 Soy el asistente de empleo.\n\n¿Cómo puedo ayudarte?\n\n1️⃣ Ver vacantes disponibles\n2️⃣ Registrarme como candidato\n3️⃣ Validar mi registro (envía tu identidad)\n\nEscribe el número o cuéntame qué necesitas 😊`;
}

// ========================================
// EXPORTAR PARA USO EN TU AGENTE
// ========================================
module.exports = {
    buscarVacantes,
    validarCandidato,
    buscarCandidatos,
    manejarMensajeWhatsApp,
    manejarSolicitudVacantes,
    manejarValidacionCandidato
};

// ========================================
// EJEMPLO DE INTEGRACIÓN CON TU SISTEMA ACTUAL
// ========================================

/**
 * Si usas ClawdBot o similar, integra así:
 */
/*
// En tu archivo principal del bot de WhatsApp

const { manejarMensajeWhatsApp } = require('./whatsapp-crm-integration');

// Cuando recibes un mensaje
client.on('message', async (msg) => {
    const from = msg.from;
    const body = msg.body;
    
    try {
        const respuesta = await manejarMensajeWhatsApp(body, from);
        await msg.reply(respuesta);
    } catch (error) {
        console.error('Error en bot WhatsApp:', error);
        await msg.reply('Disculpa, hubo un error. Intenta de nuevo.');
    }
});
*/
