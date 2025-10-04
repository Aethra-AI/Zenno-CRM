/**
 * Endpoints de WhatsApp para el CRM
 * Integración con el sistema de sesiones multi-tenant
 */

const sessionManager = require('./whatsapp-session-manager');
const express = require('express');
const router = express.Router();

/**
 * Middleware para validar tenant ID
 */
function validateTenant(req, res, next) {
    const tenantId = req.user?.id || req.headers['x-tenant-id'];
    
    if (!tenantId) {
        return res.status(401).json({
            success: false,
            error: 'Tenant ID requerido'
        });
    }
    
    req.tenantId = tenantId;
    next();
}

/**
 * @api {post} /api/whatsapp/session/init Inicializar sesión WhatsApp
 * @apiName InitWhatsAppSession
 * @apiGroup WhatsApp
 * 
 * @apiHeader {String} Authorization Bearer token del usuario
 * 
 * @apiSuccess {Boolean} success Estado de la operación
 * @apiSuccess {String} sessionId ID de la sesión (tenant ID)
 * @apiSuccess {String} status Estado de la sesión
 * @apiSuccess {String} message Mensaje descriptivo
 */
router.post('/session/init', validateTenant, async (req, res) => {
    try {
        const { tenantId } = req;
        const userId = req.user?.id;
        
        console.log(`[API] Inicializando sesión WhatsApp para tenant: ${tenantId}`);
        
        const result = await sessionManager.initializeSession(tenantId, userId);
        
        res.json(result);
        
    } catch (error) {
        console.error('Error inicializando sesión WhatsApp:', error);
        res.status(500).json({
            success: false,
            error: 'Error interno del servidor',
            message: error.message
        });
    }
});

/**
 * @api {get} /api/whatsapp/session/status Obtener estado de sesión
 * @apiName GetSessionStatus
 * @apiGroup WhatsApp
 * 
 * @apiHeader {String} Authorization Bearer token del usuario
 * 
 * @apiSuccess {Boolean} success Estado de la operación
 * @apiSuccess {Object} session Información de la sesión
 */
router.get('/session/status', validateTenant, (req, res) => {
    try {
        const { tenantId } = req;
        
        const sessionStatus = sessionManager.getSessionStatus(tenantId);
        
        if (!sessionStatus) {
            return res.json({
                success: true,
                session: null,
                message: 'No hay sesión activa'
            });
        }
        
        res.json({
            success: true,
            session: sessionStatus
        });
        
    } catch (error) {
        console.error('Error obteniendo estado de sesión:', error);
        res.status(500).json({
            success: false,
            error: 'Error interno del servidor',
            message: error.message
        });
    }
});

/**
 * @api {delete} /api/whatsapp/session/close Cerrar sesión WhatsApp
 * @apiName CloseWhatsAppSession
 * @apiGroup WhatsApp
 * 
 * @apiHeader {String} Authorization Bearer token del usuario
 * 
 * @apiSuccess {Boolean} success Estado de la operación
 * @apiSuccess {String} message Mensaje descriptivo
 */
router.delete('/session/close', validateTenant, async (req, res) => {
    try {
        const { tenantId } = req;
        
        console.log(`[API] Cerrando sesión WhatsApp para tenant: ${tenantId}`);
        
        const success = await sessionManager.closeSession(tenantId);
        
        if (success) {
            res.json({
                success: true,
                message: 'Sesión cerrada correctamente'
            });
        } else {
            res.status(404).json({
                success: false,
                error: 'No se encontró una sesión activa'
            });
        }
        
    } catch (error) {
        console.error('Error cerrando sesión WhatsApp:', error);
        res.status(500).json({
            success: false,
            error: 'Error interno del servidor',
            message: error.message
        });
    }
});

/**
 * @api {get} /api/whatsapp/chats Obtener lista de chats
 * @apiName GetChats
 * @apiGroup WhatsApp
 * 
 * @apiHeader {String} Authorization Bearer token del usuario
 * 
 * @apiSuccess {Boolean} success Estado de la operación
 * @apiSuccess {Array} chats Lista de chats
 */
router.get('/chats', validateTenant, (req, res) => {
    try {
        const { tenantId } = req;
        
        const chats = sessionManager.getTenantChats(tenantId);
        
        res.json({
            success: true,
            chats: chats
        });
        
    } catch (error) {
        console.error('Error obteniendo chats:', error);
        res.status(500).json({
            success: false,
            error: 'Error interno del servidor',
            message: error.message
        });
    }
});

/**
 * @api {get} /api/whatsapp/chats/:chatId/messages Obtener mensajes de un chat
 * @apiName GetChatMessages
 * @apiGroup WhatsApp
 * 
 * @apiHeader {String} Authorization Bearer token del usuario
 * @apiParam {String} chatId ID del chat de WhatsApp
 * 
 * @apiSuccess {Boolean} success Estado de la operación
 * @apiSuccess {Array} messages Lista de mensajes
 */
router.get('/chats/:chatId/messages', validateTenant, (req, res) => {
    try {
        const { tenantId } = req;
        const { chatId } = req.params;
        
        const messages = sessionManager.getChatHistory(tenantId, chatId);
        
        res.json({
            success: true,
            messages: messages
        });
        
    } catch (error) {
        console.error('Error obteniendo mensajes del chat:', error);
        res.status(500).json({
            success: false,
            error: 'Error interno del servidor',
            message: error.message
        });
    }
});

/**
 * @api {post} /api/whatsapp/chats/:chatId/messages Enviar mensaje
 * @apiName SendMessage
 * @apiGroup WhatsApp
 * 
 * @apiHeader {String} Authorization Bearer token del usuario
 * @apiParam {String} chatId ID del chat de WhatsApp
 * @apiBody {String} message Contenido del mensaje
 * 
 * @apiSuccess {Boolean} success Estado de la operación
 * @apiSuccess {String} messageId ID del mensaje enviado
 * @apiSuccess {String} timestamp Timestamp del envío
 */
router.post('/chats/:chatId/messages', validateTenant, async (req, res) => {
    try {
        const { tenantId } = req;
        const { chatId } = req.params;
        const { message } = req.body;
        
        if (!message || message.trim() === '') {
            return res.status(400).json({
                success: false,
                error: 'El mensaje no puede estar vacío'
            });
        }
        
        console.log(`[API] Enviando mensaje de ${tenantId} a ${chatId}`);
        
        const result = await sessionManager.sendMessage(tenantId, chatId, message);
        
        res.json({
            success: true,
            ...result
        });
        
    } catch (error) {
        console.error('Error enviando mensaje:', error);
        
        if (error.message.includes('no está lista')) {
            res.status(503).json({
                success: false,
                error: 'Sesión WhatsApp no está lista',
                message: 'Inicializa la sesión de WhatsApp primero'
            });
        } else {
            res.status(500).json({
                success: false,
                error: 'Error interno del servidor',
                message: error.message
            });
        }
    }
});

/**
 * @api {get} /api/whatsapp/sessions (Admin) Obtener todas las sesiones
 * @apiName GetAllSessions
 * @apiGroup WhatsApp
 * 
 * @apiHeader {String} Authorization Bearer token del administrador
 * 
 * @apiSuccess {Boolean} success Estado de la operación
 * @apiSuccess {Array} sessions Lista de todas las sesiones activas
 */
router.get('/sessions', (req, res) => {
    try {
        // Verificar que sea administrador
        if (req.user?.role !== 'Administrador') {
            return res.status(403).json({
                success: false,
                error: 'Acceso denegado. Solo administradores pueden ver todas las sesiones.'
            });
        }
        
        const sessions = sessionManager.getAllSessions();
        
        res.json({
            success: true,
            sessions: sessions
        });
        
    } catch (error) {
        console.error('Error obteniendo todas las sesiones:', error);
        res.status(500).json({
            success: false,
            error: 'Error interno del servidor',
            message: error.message
        });
    }
});

/**
 * WebSocket endpoint para comunicación en tiempo real
 * Se maneja en el archivo principal del servidor
 */

module.exports = router;
