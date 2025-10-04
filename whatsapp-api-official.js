/**
 * WhatsApp API Oficial Integration
 * Alternativa a WhatsApp Web usando la API oficial de Meta
 */

const axios = require('axios');

class WhatsAppOfficialAPI {
    constructor() {
        this.accessToken = process.env.WHATSAPP_ACCESS_TOKEN;
        this.phoneNumberId = process.env.WHATSAPP_PHONE_NUMBER_ID;
        this.verifyToken = process.env.WHATSAPP_VERIFY_TOKEN;
        this.webhookUrl = process.env.WHATSAPP_WEBHOOK_URL || 'https://your-domain.com/webhook';
        
        this.baseURL = `https://graph.facebook.com/v18.0/${this.phoneNumberId}`;
        
        // Mapa de sesiones por tenant
        this.tenantSessions = new Map();
        
        console.log('📱 WhatsApp Official API inicializada');
    }

    /**
     * Configura una sesión para un tenant específico
     * @param {string} tenantId - ID del tenant
     * @param {Object} config - Configuración específica del tenant
     */
    async setupTenantSession(tenantId, config = {}) {
        try {
            const sessionConfig = {
                tenantId,
                accessToken: config.accessToken || this.accessToken,
                phoneNumberId: config.phoneNumberId || this.phoneNumberId,
                webhookUrl: config.webhookUrl || this.webhookUrl,
                isActive: true,
                createdAt: new Date(),
                lastActivity: new Date(),
                messageCount: 0
            };

            this.tenantSessions.set(tenantId, sessionConfig);
            
            console.log(`[${tenantId}] ✅ Sesión WhatsApp API configurada`);
            
            return {
                success: true,
                sessionId: tenantId,
                status: 'configured',
                message: 'Sesión WhatsApp API configurada correctamente'
            };

        } catch (error) {
            console.error(`[${tenantId}] ❌ Error configurando sesión WhatsApp API:`, error);
            return {
                success: false,
                sessionId: tenantId,
                status: 'error',
                message: `Error configurando sesión: ${error.message}`
            };
        }
    }

    /**
     * Envía un mensaje de texto usando WhatsApp API oficial
     * @param {string} tenantId - ID del tenant
     * @param {string} to - Número de teléfono destino (formato internacional)
     * @param {string} message - Mensaje a enviar
     */
    async sendTextMessage(tenantId, to, message) {
        try {
            const session = this.tenantSessions.get(tenantId);
            if (!session) {
                throw new Error(`No se encontró una sesión configurada para el tenant: ${tenantId}`);
            }

            if (!session.isActive) {
                throw new Error(`La sesión del tenant ${tenantId} no está activa`);
            }

            // Formatear número de teléfono (remover caracteres especiales y agregar código país si es necesario)
            const formattedTo = this.formatPhoneNumber(to);

            const payload = {
                messaging_product: 'whatsapp',
                to: formattedTo,
                type: 'text',
                text: {
                    body: message
                }
            };

            const response = await axios.post(
                `${this.baseURL}/messages`,
                payload,
                {
                    headers: {
                        'Authorization': `Bearer ${session.accessToken}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            // Actualizar estadísticas de la sesión
            session.lastActivity = new Date();
            session.messageCount++;

            console.log(`[${tenantId}] 📤 Mensaje enviado a ${formattedTo}: ${message.substring(0, 50)}...`);

            return {
                success: true,
                messageId: response.data.messages[0].id,
                timestamp: new Date().toISOString(),
                recipient: formattedTo
            };

        } catch (error) {
            console.error(`[${tenantId}] ❌ Error enviando mensaje WhatsApp API:`, error);
            throw new Error(`Error enviando mensaje: ${error.message}`);
        }
    }

    /**
     * Envía un mensaje con plantilla usando WhatsApp API oficial
     * @param {string} tenantId - ID del tenant
     * @param {string} to - Número de teléfono destino
     * @param {string} templateName - Nombre de la plantilla
     * @param {Array} parameters - Parámetros para la plantilla
     */
    async sendTemplateMessage(tenantId, to, templateName, parameters = []) {
        try {
            const session = this.tenantSessions.get(tenantId);
            if (!session) {
                throw new Error(`No se encontró una sesión configurada para el tenant: ${tenantId}`);
            }

            const formattedTo = this.formatPhoneNumber(to);

            const payload = {
                messaging_product: 'whatsapp',
                to: formattedTo,
                type: 'template',
                template: {
                    name: templateName,
                    language: {
                        code: 'es'
                    },
                    components: parameters.length > 0 ? [
                        {
                            type: 'body',
                            parameters: parameters.map(param => ({
                                type: 'text',
                                text: param
                            }))
                        }
                    ] : []
                }
            };

            const response = await axios.post(
                `${this.baseURL}/messages`,
                payload,
                {
                    headers: {
                        'Authorization': `Bearer ${session.accessToken}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            session.lastActivity = new Date();
            session.messageCount++;

            console.log(`[${tenantId}] 📤 Plantilla enviada a ${formattedTo}: ${templateName}`);

            return {
                success: true,
                messageId: response.data.messages[0].id,
                timestamp: new Date().toISOString(),
                recipient: formattedTo,
                templateName
            };

        } catch (error) {
            console.error(`[${tenantId}] ❌ Error enviando plantilla WhatsApp API:`, error);
            throw new Error(`Error enviando plantilla: ${error.message}`);
        }
    }

    /**
     * Envía un mensaje con media usando WhatsApp API oficial
     * @param {string} tenantId - ID del tenant
     * @param {string} to - Número de teléfono destino
     * @param {string} mediaUrl - URL del archivo de media
     * @param {string} mediaType - Tipo de media (image, document, audio, video)
     * @param {string} caption - Captión opcional para el media
     */
    async sendMediaMessage(tenantId, to, mediaUrl, mediaType, caption = '') {
        try {
            const session = this.tenantSessions.get(tenantId);
            if (!session) {
                throw new Error(`No se encontró una sesión configurada para el tenant: ${tenantId}`);
            }

            const formattedTo = this.formatPhoneNumber(to);

            const payload = {
                messaging_product: 'whatsapp',
                to: formattedTo,
                type: mediaType,
                [mediaType]: {
                    link: mediaUrl,
                    ...(caption && { caption })
                }
            };

            const response = await axios.post(
                `${this.baseURL}/messages`,
                payload,
                {
                    headers: {
                        'Authorization': `Bearer ${session.accessToken}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            session.lastActivity = new Date();
            session.messageCount++;

            console.log(`[${tenantId}] 📤 Media enviado a ${formattedTo}: ${mediaType}`);

            return {
                success: true,
                messageId: response.data.messages[0].id,
                timestamp: new Date().toISOString(),
                recipient: formattedTo,
                mediaType,
                mediaUrl
            };

        } catch (error) {
            console.error(`[${tenantId}] ❌ Error enviando media WhatsApp API:`, error);
            throw new Error(`Error enviando media: ${error.message}`);
        }
    }

    /**
     * Configura el webhook para recibir mensajes
     * @param {string} tenantId - ID del tenant
     */
    async setupWebhook(tenantId) {
        try {
            const session = this.tenantSessions.get(tenantId);
            if (!session) {
                throw new Error(`No se encontró una sesión configurada para el tenant: ${tenantId}`);
            }

            const webhookConfig = {
                webhook_url: session.webhookUrl,
                verify_token: this.verifyToken,
                fields: ['messages']
            };

            const response = await axios.post(
                `${this.baseURL}/subscribed_apps`,
                webhookConfig,
                {
                    headers: {
                        'Authorization': `Bearer ${session.accessToken}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            console.log(`[${tenantId}] ✅ Webhook configurado: ${session.webhookUrl}`);

            return {
                success: true,
                webhookUrl: session.webhookUrl,
                message: 'Webhook configurado correctamente'
            };

        } catch (error) {
            console.error(`[${tenantId}] ❌ Error configurando webhook:`, error);
            throw new Error(`Error configurando webhook: ${error.message}`);
        }
    }

    /**
     * Procesa mensajes entrantes del webhook
     * @param {Object} webhookData - Datos del webhook de WhatsApp
     */
    async processIncomingMessage(webhookData) {
        try {
            if (!webhookData.entry || !webhookData.entry[0] || !webhookData.entry[0].changes) {
                return { processed: false, reason: 'Formato de webhook inválido' };
            }

            const changes = webhookData.entry[0].changes[0];
            if (!changes.value || !changes.value.messages) {
                return { processed: false, reason: 'No hay mensajes en el webhook' };
            }

            const message = changes.value.messages[0];
            const contact = changes.value.contacts[0];
            const from = message.from;
            const messageText = message.text?.body || '';
            const messageType = message.type;
            const timestamp = parseInt(message.timestamp);

            // Determinar tenant basado en el número de teléfono de la empresa
            const tenantId = this.getTenantFromPhoneNumber(changes.value.metadata.phone_number_id);

            const processedMessage = {
                id: message.id,
                from: from,
                contactName: contact?.profile?.name || from,
                message: messageText,
                type: messageType,
                timestamp: timestamp,
                tenantId: tenantId,
                rawMessage: message
            };

            console.log(`[${tenantId}] 📨 Mensaje recibido de ${from}: ${messageText.substring(0, 50)}...`);

            return {
                processed: true,
                message: processedMessage,
                tenantId: tenantId
            };

        } catch (error) {
            console.error('❌ Error procesando mensaje entrante:', error);
            return { processed: false, reason: error.message };
        }
    }

    /**
     * Obtiene el estado de una sesión
     * @param {string} tenantId - ID del tenant
     */
    getSessionStatus(tenantId) {
        const session = this.tenantSessions.get(tenantId);
        
        if (!session) {
            return null;
        }

        return {
            sessionId: tenantId,
            status: session.isActive ? 'active' : 'inactive',
            isReady: session.isActive,
            lastActivity: session.lastActivity.toISOString(),
            createdAt: session.createdAt.toISOString(),
            messageCount: session.messageCount,
            phoneNumberId: session.phoneNumberId
        };
    }

    /**
     * Obtiene todas las sesiones activas
     */
    getAllSessions() {
        const sessions = [];
        
        for (const [tenantId, session] of this.tenantSessions) {
            sessions.push({
                tenantId,
                status: session.isActive ? 'active' : 'inactive',
                isReady: session.isActive,
                lastActivity: session.lastActivity.toISOString(),
                createdAt: session.createdAt.toISOString(),
                messageCount: session.messageCount,
                phoneNumberId: session.phoneNumberId
            });
        }
        
        return sessions;
    }

    /**
     * Desactiva una sesión
     * @param {string} tenantId - ID del tenant
     */
    deactivateSession(tenantId) {
        const session = this.tenantSessions.get(tenantId);
        
        if (session) {
            session.isActive = false;
            console.log(`[${tenantId}] 🔌 Sesión WhatsApp API desactivada`);
            return true;
        }
        
        return false;
    }

    /**
     * Formatea un número de teléfono para WhatsApp API
     * @param {string} phoneNumber - Número de teléfono
     */
    formatPhoneNumber(phoneNumber) {
        // Remover todos los caracteres no numéricos
        let cleaned = phoneNumber.replace(/\D/g, '');
        
        // Si no tiene código de país, agregar +504 (Honduras)
        if (cleaned.length === 8) {
            cleaned = '504' + cleaned;
        }
        
        // Si empieza con +, removerlo
        if (cleaned.startsWith('+')) {
            cleaned = cleaned.substring(1);
        }
        
        return cleaned;
    }

    /**
     * Determina el tenant basado en el phone number ID
     * @param {string} phoneNumberId - ID del número de teléfono
     */
    getTenantFromPhoneNumber(phoneNumberId) {
        // Buscar en las sesiones cuál tiene este phone number ID
        for (const [tenantId, session] of this.tenantSessions) {
            if (session.phoneNumberId === phoneNumberId) {
                return tenantId;
            }
        }
        
        // Si no se encuentra, usar un tenant por defecto
        return 'default';
    }

    /**
     * Verifica la configuración de la API
     */
    async verifyConfiguration() {
        try {
            const response = await axios.get(
                `${this.baseURL}`,
                {
                    headers: {
                        'Authorization': `Bearer ${this.accessToken}`
                    }
                }
            );

            return {
                success: true,
                phoneNumber: response.data.display_phone_number,
                verified: response.data.verified_name,
                status: response.data.code_verification_status
            };

        } catch (error) {
            console.error('❌ Error verificando configuración WhatsApp API:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
}

// Exportar singleton
module.exports = new WhatsAppOfficialAPI();
