/**
 * WhatsApp Session Manager para CRM Multi-Tenant
 * Gestiona sesiones de WhatsApp por tenant con aislamiento completo
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const path = require('path');
const fs = require('fs');

class WhatsAppSessionManager {
    constructor() {
        // Mapa de sesiones activas: Map<tenantId, SessionInfo>
        this.activeSessions = new Map();

        // Mapa de WebSocket connections por tenant
        this.tenantWebSockets = new Map();

        // Configuración de sesiones
        this.sessionConfig = {
            puppeteerOptions: {
                headless: true,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-notifications',
                    '--disable-extensions',
                    '--disable-infobars',
                    '--window-size=1920,1080',
                    '--disable-blink-features=AutomationControlled',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                ]
            }
        };

        // Crear directorio de sesiones si no existe
        this.ensureSessionsDirectory();
    }

    /**
     * Asegura que el directorio de sesiones existe
     */
    ensureSessionsDirectory() {
        const sessionsDir = path.join(__dirname, 'sessions');
        if (!fs.existsSync(sessionsDir)) {
            fs.mkdirSync(sessionsDir, { recursive: true });
            console.log('📁 Directorio de sesiones creado:', sessionsDir);
        }
    }

    /**
     * Inicializa una nueva sesión de WhatsApp para un tenant específico
     * @param {string} tenantId - ID del tenant (ID del usuario del CRM)
     * @param {string} userId - ID del usuario del CRM
     * @returns {Promise<Object>} Estado de la sesión
     */
    async initializeSession(tenantId, userId) {
        // Verificar si ya existe una sesión activa para este tenant
        if (this.activeSessions.has(tenantId)) {
            const existingSession = this.activeSessions.get(tenantId);
            return {
                success: true,
                sessionId: tenantId,
                status: existingSession.status,
                message: 'Sesión ya activa',
                qrCode: existingSession.qrCode,
                isReady: existingSession.status === 'ready'
            };
        }

        try {
            console.log(`[${tenantId}] 🚀 Inicializando sesión WhatsApp para tenant: ${tenantId}`);

            // Crear directorio específico para este tenant
            const tenantSessionsDir = path.join(__dirname, 'sessions', tenantId);
            if (!fs.existsSync(tenantSessionsDir)) {
                fs.mkdirSync(tenantSessionsDir, { recursive: true });
            }

            // Crear cliente WhatsApp con configuración específica del tenant
            const client = new Client({
                authStrategy: new LocalAuth({
                    clientId: `crm-tenant-${tenantId}`,
                    dataPath: tenantSessionsDir,
                }),
                puppeteer: this.sessionConfig.puppeteerOptions,
            });

            // Crear objeto de sesión
            const sessionInfo = {
                tenantId,
                userId,
                client,
                status: 'initializing',
                qrCode: null,
                lastActivity: new Date(),
                createdAt: new Date(),
                chatContext: {},
                messageHistory: new Map(), // Historial de mensajes por chat
                isReady: false
            };

            // Almacenar la sesión
            this.activeSessions.set(tenantId, sessionInfo);

            // Configurar event handlers
            this.setupEventHandlers(client, tenantId);

            // Inicializar el cliente
            await client.initialize();

            return {
                success: true,
                sessionId: tenantId,
                status: 'initializing',
                message: 'Sesión inicializada correctamente'
            };

        } catch (error) {
            console.error(`[${tenantId}] ❌ Error al inicializar sesión:`, error);

            // Limpiar la sesión en caso de error
            this.activeSessions.delete(tenantId);

            return {
                success: false,
                sessionId: tenantId,
                status: 'error',
                message: `Error al inicializar: ${error.message}`
            };
        }
    }

    /**
     * Configura los event handlers para un cliente específico
     * @param {Client} client - Cliente de WhatsApp
     * @param {string} tenantId - ID del tenant
     */
    setupEventHandlers(client, tenantId) {
        const sessionInfo = this.activeSessions.get(tenantId);
        if (!sessionInfo) return;

        // Evento: Código QR generado
        client.on('qr', async (qr) => {
            console.log(`[${tenantId}] 🔑 Código QR generado`);
            try {
                // Generar imagen QR como base64
                const qrImageBase64 = await qrcode.toDataURL(qr, {
                    width: 256,
                    margin: 2,
                    color: {
                        dark: '#000000',
                        light: '#FFFFFF'
                    }
                });

                sessionInfo.qrCode = qrImageBase64;
                sessionInfo.status = 'qr_ready';

                this.notifyTenantWebSocket(tenantId, {
                    type: 'qr_ready',
                    qrCode: qrImageBase64,
                    message: 'Escanea el código QR con tu WhatsApp'
                });
            } catch (error) {
                console.error(`[${tenantId}] Error generando QR como imagen:`, error);
                // Fallback: usar QR como texto
                sessionInfo.qrCode = qr;
                sessionInfo.status = 'qr_ready';

                this.notifyTenantWebSocket(tenantId, {
                    type: 'qr_ready',
                    qrCode: qr,
                    message: 'Escanea el código QR con tu WhatsApp'
                });
            }
        });

        // Evento: Autenticación exitosa
        client.on('authenticated', () => {
            console.log(`[${tenantId}] ✅ Autenticación exitosa`);
            sessionInfo.status = 'authenticated';
            this.notifyTenantWebSocket(tenantId, {
                type: 'authenticated',
                message: 'Sesión autenticada correctamente'
            });
        });

        // Evento: Error de autenticación
        client.on('auth_failure', (msg) => {
            console.error(`[${tenantId}] ❌ Error de autenticación:`, msg);
            sessionInfo.status = 'auth_failed';
            this.notifyTenantWebSocket(tenantId, {
                type: 'auth_failed',
                message: `Error de autenticación: ${msg}`
            });
        });

        // Evento: Cliente listo
        client.on('ready', async () => {
            console.log(`[${tenantId}] 🚀 Cliente WhatsApp listo`);
            sessionInfo.status = 'ready';
            sessionInfo.isReady = true;
            sessionInfo.lastActivity = new Date();

            this.notifyTenantWebSocket(tenantId, {
                type: 'ready',
                message: 'WhatsApp conectado y listo'
            });

            // Configurar manejadores de mensajes
            this.setupMessageHandlers(client, tenantId);
        });

        // Evento: Desconexión
        client.on('disconnected', (reason) => {
            console.log(`[${tenantId}] 🔌 Cliente desconectado:`, reason);
            sessionInfo.status = 'disconnected';
            sessionInfo.isReady = false;
            this.notifyTenantWebSocket(tenantId, {
                type: 'disconnected',
                message: `Desconectado: ${reason}`
            });

            // Limpiar sesión después de desconexión
            this.cleanupSession(tenantId);
        });

        // Evento: Mensaje recibido
        client.on('message', async (message) => {
            await this.handleIncomingMessage(message, tenantId);
        });
    }

    /**
     * Configura los manejadores de mensajes para un cliente
     * @param {Client} client - Cliente de WhatsApp
     * @param {string} tenantId - ID del tenant
     */
    setupMessageHandlers(client, tenantId) {
        // Los manejadores de mensajes se configuran en setupEventHandlers
        // para mantener la consistencia
    }

    /**
     * Maneja mensajes entrantes
     * @param {Message} message - Mensaje de WhatsApp
     * @param {string} tenantId - ID del tenant
     */
    async handleIncomingMessage(message, tenantId) {
        try {
            const sessionInfo = this.activeSessions.get(tenantId);
            if (!sessionInfo) return;

            const chatId = message.from;
            const messageData = {
                id: message.id.id,
                chatId: chatId,
                body: message.body,
                timestamp: message.timestamp,
                fromMe: message.fromMe,
                hasMedia: message.hasMedia,
                type: message.type,
                sender: message.fromMe ? 'me' : 'contact'
            };

            // Actualizar historial de mensajes
            if (!sessionInfo.messageHistory.has(chatId)) {
                sessionInfo.messageHistory.set(chatId, []);
            }
            sessionInfo.messageHistory.get(chatId).push(messageData);

            // Notificar al WebSocket del tenant
            this.notifyTenantWebSocket(tenantId, {
                type: 'new_message',
                message: messageData,
                chatId: chatId
            });

            // Actualizar última actividad
            sessionInfo.lastActivity = new Date();

            console.log(`[${tenantId}] 📨 Mensaje recibido de ${chatId}: ${message.body?.substring(0, 50)}...`);

        } catch (error) {
            console.error(`[${tenantId}] ❌ Error manejando mensaje entrante:`, error);
        }
    }

    /**
     * Envía un mensaje a través de la sesión del tenant
     * @param {string} tenantId - ID del tenant
     * @param {string} chatId - ID del chat de WhatsApp
     * @param {string} message - Contenido del mensaje
     * @returns {Promise<Object>} Resultado de la operación
     */
    async sendMessage(tenantId, chatId, message) {
        const sessionInfo = this.activeSessions.get(tenantId);

        if (!sessionInfo) {
            throw new Error(`No se encontró una sesión activa para el tenant: ${tenantId}`);
        }

        if (!sessionInfo.isReady) {
            throw new Error(`La sesión del tenant ${tenantId} no está lista. Estado: ${sessionInfo.status}`);
        }

        try {
            // Formatear chatId si es necesario
            const formattedChatId = chatId.endsWith('@c.us') ? chatId : `${chatId}@c.us`;

            // Enviar el mensaje
            const sentMessage = await sessionInfo.client.sendMessage(formattedChatId, message);

            // Actualizar última actividad
            sessionInfo.lastActivity = new Date();

            // Crear objeto de mensaje enviado
            const messageData = {
                id: sentMessage.id.id,
                chatId: formattedChatId,
                body: message,
                timestamp: Math.floor(Date.now() / 1000),
                fromMe: true,
                hasMedia: false,
                type: 'text',
                sender: 'me'
            };

            // Actualizar historial
            if (!sessionInfo.messageHistory.has(formattedChatId)) {
                sessionInfo.messageHistory.set(formattedChatId, []);
            }
            sessionInfo.messageHistory.get(formattedChatId).push(messageData);

            // Notificar al WebSocket del tenant
            this.notifyTenantWebSocket(tenantId, {
                type: 'message_sent',
                message: messageData,
                chatId: formattedChatId
            });

            console.log(`[${tenantId}] 📤 Mensaje enviado a ${formattedChatId}: ${message.substring(0, 50)}...`);

            return {
                success: true,
                messageId: sentMessage.id.id,
                timestamp: new Date().toISOString(),
                chatId: formattedChatId
            };

        } catch (error) {
            console.error(`[${tenantId}] ❌ Error enviando mensaje a ${chatId}:`, error);
            throw new Error(`Error enviando mensaje: ${error.message}`);
        }
    }

    /**
     * Obtiene el estado de una sesión
     * @param {string} tenantId - ID del tenant
     * @returns {Object|null} Estado de la sesión
     */
    getSessionStatus(tenantId) {
        const sessionInfo = this.activeSessions.get(tenantId);

        if (!sessionInfo) {
            return null;
        }

        return {
            sessionId: tenantId,
            status: sessionInfo.status,
            isReady: sessionInfo.isReady,
            qrCode: sessionInfo.qrCode,
            lastActivity: sessionInfo.lastActivity.toISOString(),
            createdAt: sessionInfo.createdAt.toISOString(),
            totalChats: sessionInfo.messageHistory.size
        };
    }

    /**
     * Obtiene todas las sesiones activas
     * @returns {Array} Lista de sesiones activas
     */
    getAllSessions() {
        const sessions = [];

        for (const [tenantId, sessionInfo] of this.activeSessions) {
            sessions.push({
                tenantId,
                status: sessionInfo.status,
                isReady: sessionInfo.isReady,
                lastActivity: sessionInfo.lastActivity.toISOString(),
                createdAt: sessionInfo.createdAt.toISOString(),
                totalChats: sessionInfo.messageHistory.size
            });
        }

        return sessions;
    }

    /**
     * Cierra una sesión específica
     * @param {string} tenantId - ID del tenant
     * @returns {Promise<boolean>} Éxito de la operación
     */
    async closeSession(tenantId) {
        const sessionInfo = this.activeSessions.get(tenantId);

        if (!sessionInfo) {
            return false;
        }

        try {
            console.log(`[${tenantId}] 🧹 Cerrando sesión WhatsApp`);

            // Destruir el cliente
            await sessionInfo.client.destroy();

            // Limpiar la sesión
            this.activeSessions.delete(tenantId);

            // Notificar al WebSocket del tenant
            this.notifyTenantWebSocket(tenantId, {
                type: 'session_closed',
                message: 'Sesión cerrada correctamente'
            });

            console.log(`[${tenantId}] ✅ Sesión cerrada correctamente`);
            return true;

        } catch (error) {
            console.error(`[${tenantId}] ❌ Error cerrando sesión:`, error);
            return false;
        }
    }

    /**
     * Limpia una sesión después de desconexión
     * @param {string} tenantId - ID del tenant
     */
    cleanupSession(tenantId) {
        console.log(`[${tenantId}] 🧹 Limpiando sesión`);
        this.activeSessions.delete(tenantId);
    }

    /**
     * Registra un WebSocket para un tenant específico
     * @param {string} tenantId - ID del tenant
     * @param {WebSocket} ws - Conexión WebSocket
     */
    registerTenantWebSocket(tenantId, ws) {
        this.tenantWebSockets.set(tenantId, ws);
        console.log(`[${tenantId}] 🔌 WebSocket registrado para tenant`);
    }

    /**
     * Desregistra un WebSocket de un tenant
     * @param {string} tenantId - ID del tenant
     */
    unregisterTenantWebSocket(tenantId) {
        this.tenantWebSockets.delete(tenantId);
        console.log(`[${tenantId}] 🔌 WebSocket desregistrado para tenant`);
    }

    /**
     * Notifica a un tenant específico via WebSocket
     * @param {string} tenantId - ID del tenant
     * @param {Object} data - Datos a enviar
     */
    notifyTenantWebSocket(tenantId, data) {
        const ws = this.tenantWebSockets.get(tenantId);

        if (ws && ws.readyState === 1) { // WebSocket.OPEN
            try {
                ws.send(JSON.stringify({
                    tenantId,
                    timestamp: new Date().toISOString(),
                    ...data
                }));
            } catch (error) {
                console.error(`[${tenantId}] ❌ Error enviando notificación WebSocket:`, error);
                this.unregisterTenantWebSocket(tenantId);
            }
        }
    }

    /**
     * Obtiene el historial de mensajes de un chat específico
     * @param {string} tenantId - ID del tenant
     * @param {string} chatId - ID del chat
     * @returns {Array} Historial de mensajes
     */
    getChatHistory(tenantId, chatId) {
        const sessionInfo = this.activeSessions.get(tenantId);

        if (!sessionInfo) {
            return [];
        }

        return sessionInfo.messageHistory.get(chatId) || [];
    }

    /**
     * Obtiene todos los chats de un tenant
     * @param {string} tenantId - ID del tenant
     * @returns {Array} Lista de chats
     */
    getTenantChats(tenantId) {
        const sessionInfo = this.activeSessions.get(tenantId);

        if (!sessionInfo) {
            return [];
        }

        const chats = [];

        for (const [chatId, messages] of sessionInfo.messageHistory) {
            const lastMessage = messages[messages.length - 1];
            chats.push({
                chatId,
                lastMessage: lastMessage ? {
                    body: lastMessage.body,
                    timestamp: lastMessage.timestamp,
                    fromMe: lastMessage.fromMe
                } : null,
                messageCount: messages.length
            });
        }

        // Ordenar por último mensaje
        chats.sort((a, b) => {
            if (!a.lastMessage && !b.lastMessage) return 0;
            if (!a.lastMessage) return 1;
            if (!b.lastMessage) return -1;
            return b.lastMessage.timestamp - a.lastMessage.timestamp;
        });

        return chats;
    }
}

// Exportar singleton
module.exports = new WhatsAppSessionManager();
