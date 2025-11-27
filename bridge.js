let analysisQueue = new Set(); // Una cola para chats que necesitan análisis (Set evita duplicados)
let isAnalysisRunning = false; // Un semáforo para evitar ejecuciones simultáneas

// =================================================================
// --- 2. CONFIGURACIÓN INICIAL ---
// =================================================================

// Importaciones básicas
const express = require('express');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const qrcodeTerminal = require('qrcode-terminal');
const WebSocket = require('ws');
const WebSocketServer = WebSocket.Server;
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');
const moment = require('moment-timezone');
const { v4: uuidv4 } = require('uuid');
const axios = require('axios');
const cors = require('cors');
const bodyParser = require('body-parser');
const { Configuration, OpenAIApi } = require('openai');
const OpenAI = require('openai').default;
const FormData = require('form-data');
const multer = require('multer');
const upload = multer();
const fetch = require('node-fetch');

// Inicializar la aplicación Express
const app = express();
app.use(cors());
app.use(express.json());
app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '50mb' }));

// Variables globales
let crmSocket = null; // Socket WebSocket para la comunicación con el CRM
const activeSessions = new Map(); // Almacena las sesiones activas: Map<sessionId, {client, status, tenantId, lastActivity, proxy, qrCode}>
const webSocketClients = new Map(); // Mapa para mantener múltiples conexiones WebSocket

// Inicializar clientes de IA
let openai, genAI, geminiModel;

try {
    if (process.env.OPENAI_API_KEY) {
        openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
        console.log('✅ Cliente OpenAI inicializado');
    } else {
        console.warn('⚠️  OPENAI_API_KEY no configurada. Funciones de IA deshabilitadas.');
    }

    if (process.env.GEMINI_API_KEY) {
        const { GoogleGenerativeAI } = require('@google/generative-ai');
        genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
        geminiModel = genAI.getGenerativeModel({ model: "gemini-1.5-flash-latest" });
        console.log('✅ Cliente Gemini inicializado');
    } else {
        console.warn('⚠️  GEMINI_API_KEY no configurada. Análisis con Gemini deshabilitado.');
    }
} catch (error) {
    console.error('Error al inicializar clientes de IA:', error);
    console.warn('⚠️  Continuando sin funciones de IA...');
}

// Configuración de Clientes de IA se inicializa en el bloque try-catch

// =================================================================
// --- PUENTE Y SERVIDOR DE CHATBOT UNIFICADO PARA CRM HENMIR v3.4 FINAL ---
// =================================================================

console.log('Iniciando el cerebro de comunicación del CRM...');

// --- Configuración de Proxies ---
const PROXY_LIST = [
    // Agrega aquí tus proxies en el formato:
    // {"server": "host:port", "username": "user", "password": "pass"},
    // Ejemplo:
    // {"server": "proxy1.example.com:8080", "username": "user1", "password": "pass123"},
    // {"server": "proxy2.example.com:8080", "username": "user2", "password": "pass456"}
];

/**
 * Asigna un proxy único a una sesión de manera determinista
 * @param {string} sessionId - ID único de la sesión
 * @returns {Object|null} Objeto de configuración del proxy o null si no hay proxies
 */
function getUniqueProxyForSession(sessionId) {
    if (!PROXY_LIST.length) return null;

    // Función hash simple para convertir el sessionId en un número
    const hash = sessionId.split('').reduce((acc, char) => {
        return (acc << 5) - acc + char.charCodeAt(0);
    }, 0);

    const proxyIndex = Math.abs(hash) % PROXY_LIST.length;
    return PROXY_LIST[proxyIndex];
}

// --- Gestor Centralizado de Clientes ---
// Importar el nuevo sistema de gestión de sesiones
const sessionManager = require('./whatsapp-session-manager');

// activeSessions ya está definido arriba (mantener para compatibilidad)

/**
 * Inicializa una nueva sesión de WhatsApp
 * @param {string} sessionId - ID único de la sesión
 * @param {string} [tenantId] - ID del tenant (opcional)
 * @returns {Promise<Object>} Estado de la sesión
 */
async function startSession(sessionId, tenantId = 'default') {
    // Si ya existe una sesión activa, la retornamos
    if (activeSessions.has(sessionId)) {
        return {
            sessionId,
            status: 'already_running',
            message: 'La sesión ya está activa'
        };
    }

    // Configuración del proxy
    const proxyConfig = getUniqueProxyForSession(sessionId);
    const puppeteerOptions = {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--disable-gpu'
        ]
    };

    // Configuración de path de Chromium para entornos Linux/Server (Oracle Cloud)
    if (process.env.PUPPETEER_EXECUTABLE_PATH) {
        puppeteerOptions.executablePath = process.env.PUPPETEER_EXECUTABLE_PATH;
    } else if (process.platform === 'linux') {
        // Rutas comunes en Ubuntu/Debian
        const commonPaths = ['/usr/bin/chromium-browser', '/usr/bin/chromium', '/snap/bin/chromium'];
        for (const p of commonPaths) {
            if (fs.existsSync(p)) {
                console.log(`[${sessionId}] 🐧 Usando Chromium en: ${p}`);
                puppeteerOptions.executablePath = p;
                break;
            }
        }
    }

    if (!puppeteerOptions.executablePath) {
        console.log(`[${sessionId}] ℹ️  Usando Chromium empaquetado con Puppeteer`);
    }

    // Configuración de Puppeteer para evitar detección
    puppeteerOptions.args.push(
        '--disable-software-rasterizer',
        '--disable-notifications',
        '--disable-extensions',
        '--disable-infobars',
        '--window-size=1920,1080',
        '--disable-blink-features=AutomationControlled',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    );

    // Configuración del proxy si está disponible
    if (proxyConfig) {
        const { server, username, password } = proxyConfig;
        const auth = username && password ? `${username}:${password}@` : '';
        const proxyUrl = `http://${auth}${server}`;

        console.log(`[${sessionId}] 🌐 Usando proxy: ${server}`);
        puppeteerOptions.args.push(`--proxy-server=${proxyUrl}`);

        if (username && password) {
            puppeteerOptions.args.push(`--proxy-auth=${username}:${password}`);
        }
    } else {
        console.log(`[${sessionId}] ⚠️  No se configuró ningún proxy. Usando conexión directa.`);
    }

    // Crear una nueva instancia del cliente
    const client = new Client({
        authStrategy: new LocalAuth({
            clientId: `crm-whatsapp-${sessionId}`,
            dataPath: `./sessions/${tenantId}`,
        }),
        puppeteer: puppeteerOptions,
    });

    // Inicializar el estado de la sesión
    const sessionState = {
        client,
        status: 'initializing',
        lastActivity: new Date(),
        chatContext: {},
        tenantId,
        proxy: proxyConfig ? `${proxyConfig.server}` : 'direct'
    };

    // Almacenar la sesión
    // Almacenar el estado de la sesión
    activeSessions.set(sessionId, sessionState);

    // Configurar manejadores de eventos
    setupClientEventHandlers(client, sessionId);

    // Inicializar el cliente
    try {
        await client.initialize();
        return {
            sessionId,
            status: 'initialized',
            message: 'Sesión inicializada correctamente',
        };
    } catch (error) {
        console.error(`[${sessionId}] ❌ Error al inicializar la sesión:`, error);
        activeSessions.delete(sessionId);
        throw error;
    }
}

/**
 * Configura los manejadores de eventos para un cliente de WhatsApp
 * @param {Client} client - Instancia del cliente de WhatsApp
 * @param {string} sessionId - ID de la sesión
 */
function setupClientEventHandlers(client, sessionId) {
    const session = activeSessions.get(sessionId);
    if (!session) return;

    client.on('qr', (qr) => {
        console.log(`[${sessionId}] 🔑 Escanea el código QR`);
        session.status = 'qr_ready';
        session.qrCode = qr;
        notifyStatusUpdate(sessionId, 'qr_ready', 'Por favor, escanea el código QR');
    });

    client.on('authenticated', () => {
        console.log(`[${sessionId}] ✅ Autenticación exitosa`);
        session.status = 'authenticated';
        notifyStatusUpdate(sessionId, 'authenticated', 'Sesión autenticada correctamente');
    });

    client.on('auth_failure', (msg) => {
        console.error(`[${sessionId}] ❌ Error de autenticación:`, msg);
        session.status = 'auth_failed';
        notifyStatusUpdate(sessionId, 'auth_failed', 'Error en la autenticación: ' + msg);
        cleanupSession(sessionId);
    });

    client.on('ready', () => {
        console.log(`[${sessionId}] 🚀 Cliente de WhatsApp listo`);
        session.status = 'ready';
        session.lastActivity = new Date();
        notifyStatusUpdate(sessionId, 'ready', 'Cliente listo para enviar mensajes');

        // Configurar manejadores de mensajes
        setupMessageHandlers(client, sessionId);
    });

    client.on('disconnected', (reason) => {
        console.log(`[${sessionId}] 🔌 Cliente desconectado:`, reason);
        session.status = 'disconnected';
        notifyStatusUpdate(sessionId, 'disconnected', `Cliente desconectado: ${reason}`);
        cleanupSession(sessionId);
    });
}

/**
 * Configura los manejadores de mensajes para un cliente
 * @param {Client} client - Instancia del cliente de WhatsApp
 * @param {string} sessionId - ID de la sesión
 */
function setupMessageHandlers(client, sessionId) {
    client.on('message', async (msg) => {
        const session = activeSessions.get(sessionId);
        if (!session) return;

        session.lastActivity = new Date();

        // Aquí iría la lógica de procesamiento de mensajes
        // ...

        // Notificar al frontend sobre el nuevo mensaje
        notifyNewMessage(sessionId, msg);
    });
}

/**
 * Notifica un cambio de estado a través del WebSocket
 * @param {string} sessionId - ID de la sesión
 * @param {string} status - Nuevo estado
 * @param {string} message - Mensaje descriptivo
 */
function notifyStatusUpdate(sessionId, status, message) {
    const session = activeSessions.get(sessionId);
    if (!session) return;

    const statusUpdate = {
        type: 'status_update',
        sessionId,
        status,
        message,
        timestamp: new Date().toISOString(),
        proxy: session.proxy,
        tenantId: session.tenantId
    };

    // Enviar a través del WebSocket si está disponible
    if (crmSocket && crmSocket.readyState === WebSocket.OPEN) {
        crmSocket.send(JSON.stringify(statusUpdate));
    }

    console.log(`[${sessionId}] 📢 Estado actualizado:`, status, '-', message);
}

/**
 * Limpia los recursos de una sesión
 * @param {string} sessionId - ID de la sesión a limpiar
 */
async function cleanupSession(sessionId) {
    const session = activeSessions.get(sessionId);
    if (!session) return;

    try {
        if (session.client) {
            await session.client.destroy();
        }
    } catch (error) {
        console.error(`[${sessionId}] Error al limpiar la sesión:`, error);
    } finally {
        activeSessions.delete(sessionId);
        console.log(`[${sessionId}] 🧹 Sesión limpiada`);
    }
}

// ... todas tus importaciones existentes (require) ...

// --- NUEVO: SOLUCIÓN PARA EL PROBLEMA DE LA TERMINAL CONGELADA ---
// --- NUEVO: SOLUCIÓN PARA EL PROBLEMA DE LA TERMINAL CONGELADA ---
const readline = require('readline');

// Evita que el proceso se cierre inmediatamente en Windows
if (process.platform === "win32") {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    rl.on("SIGINT", function () {
        process.emit("SIGINT");
    });
}

// Capturamos el evento Ctrl+C (SIGINT) de forma limpia
process.on("SIGINT", () => {
    console.log("\nCerrando el puente de comunicación de forma segura...");
    // Aquí podrías añadir lógica de limpieza si la tuvieras, como cerrar la BD
    db.close((err) => {
        if (err) {
            console.error("Error al cerrar la base de datos SQLite:", err.message);
        } else {
            console.log("Base de datos SQLite cerrada.");
        }
        process.exit(0);
    });
});

// =================================================================
// CONFIGURACIÓN DE DB
// =================================================================

/**
 * Inicia el servidor HTTP y restaura las sesiones existentes
 */
async function startServer() {
    try {
        // Crear directorio de sesiones si no existe
        const sessionsDir = path.join(__dirname, 'sessions');
        if (!fs.existsSync(sessionsDir)) {
            fs.mkdirSync(sessionsDir, { recursive: true });
        }

        // Iniciar el servidor HTTP
        const PORT = process.env.PORT || 3000;
        const server = app.listen(PORT, async () => {
            console.log(`✅ Servidor Express escuchando en http://localhost:${PORT}`);

            // Probar conectividad
            try {
                const res = await fetch('https://www.google.com', { method: 'HEAD' });
                console.log(res.ok ? "✅ Prueba de conectividad exitosa." : "❌ Prueba de conectividad fallida.");
            } catch (err) {
                console.error("❌ FALLO CRÍTICO de conectividad:", err.message);
            }

            // Configurar WebSocket
            setupWebSocketServer(server);

            // Restaurar sesiones existentes
            await restoreSessions();
        });

        // Manejar cierre limpio
        process.on('SIGTERM', () => {
            console.log('🛑 Recibida señal SIGTERM. Cerrando servidor...');
            shutdown(server);
        });

        process.on('SIGINT', () => {
            console.log('🛑 Recibida señal SIGINT. Cerrando servidor...');
            shutdown(server);
        });

        // Manejar errores no capturados
        process.on('uncaughtException', (error) => {
            console.error('🔥 Error no capturado:', error);
            shutdown(server, 1);
        });

        process.on('unhandledRejection', (reason) => {
            console.error('🔥 Promesa rechazada no manejada:', reason);
        });

    } catch (error) {
        console.error('❌ Error al iniciar el servidor:', error);
        process.exit(1);
    }
}

/**
 * Restaura las sesiones guardadas al iniciar el servidor
 */
async function restoreSessions() {
    try {
        const sessionsDir = path.join(__dirname, 'sessions');

        // Verificar si el directorio existe
        if (!fs.existsSync(sessionsDir)) {
            console.log('ℹ️  No hay sesiones previas para restaurar');
            return;
        }

        // Leer los directorios de tenant
        const tenantDirs = fs.readdirSync(sessionsDir, { withFileTypes: true })
            .filter(dirent => dirent.isDirectory())
            .map(dirent => dirent.name);

        console.log(`🔍 Buscando sesiones en ${tenantDirs.length} directorios de tenant...`);

        let restoredCount = 0;

        // Procesar cada directorio de tenant
        for (const tenantId of tenantDirs) {
            const tenantDir = path.join(sessionsDir, tenantId);
            const sessionDirs = fs.readdirSync(tenantDir, { withFileTypes: true })
                .filter(dirent => dirent.isDirectory())
                .map(dirent => dirent.name);

            console.log(`🔄 Procesando ${sessionDirs.length} sesiones para el tenant ${tenantId}...`);

            // Iniciar cada sesión
            for (const sessionId of sessionDirs) {
                try {
                    console.log(`🔄 Restaurando sesión ${sessionId}...`);
                    await startSession(sessionId, tenantId);
                    restoredCount++;
                } catch (error) {
                    console.error(`❌ Error al restaurar la sesión ${sessionId}:`, error.message);
                }
            }
        }

        console.log(`✅ Restauración completada. ${restoredCount} sesiones restauradas.`);

    } catch (error) {
        console.error('❌ Error al restaurar sesiones:', error);
    }
}

/**
 * Cierra el servidor de forma controlada
 * @param {Object} server - Instancia del servidor HTTP
 * @param {number} [exitCode=0] - Código de salida
 */
async function shutdown(server, exitCode = 0) {
    console.log('🛑 Cerrando servidor...');

    try {
        // Cerrar todas las sesiones de WhatsApp
        const closePromises = [];
        for (const [sessionId] of activeSessions) {
            closePromises.push(cleanupSession(sessionId));
        }

        await Promise.all(closePromises);

        // Cerrar la base de datos
        if (db) {
            await new Promise((resolve) => {
                db.close((err) => {
                    if (err) console.error('Error al cerrar la base de datos:', err);
                    resolve();
                });
            });
        }

        // Cerrar el servidor HTTP
        if (server) {
            await new Promise((resolve) => {
                server.close(() => {
                    console.log('✅ Servidor cerrado correctamente');
                    resolve();
                });
            });
        }

    } catch (error) {
        console.error('Error durante el cierre:', error);
    } finally {
        process.exit(exitCode);
    }
}


// =================================================================
// VERIFICA QUE TU BLOQUE DE DB SEA EXACTAMENTE ASÍ
// =================================================================
const db = new sqlite3.Database('./whatsapp_chats.db', (err) => {
    if (err) {
        console.error("❌ Error CRÍTICO al abrir la base de datos:", err.message);
        return;
    }
    console.log("✅ Conectado a SQLite.");

    db.serialize(() => {
        console.log("--- Iniciando configuración de la base de datos ---");

        // PASO 1: Crear todas las tablas
        db.run(`CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT, sender TEXT, body TEXT, timestamp INTEGER, from_me BOOLEAN)`);
        db.run(`CREATE TABLE IF NOT EXISTS conversations (chat_id TEXT PRIMARY KEY, contact_name TEXT, last_message_timestamp INTEGER, bot_active BOOLEAN NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'new_visitor', known_identity TEXT, custom_name TEXT, chat_type TEXT NOT NULL DEFAULT 'unassigned', is_pinned BOOLEAN NOT NULL DEFAULT 0, unread_count INTEGER NOT NULL DEFAULT 0, context_city TEXT, context_area TEXT)`);
        db.run(`CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)`);
        db.run(`CREATE TABLE IF NOT EXISTS chat_tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, color TEXT DEFAULT '#808080')`);
        db.run(`CREATE TABLE IF NOT EXISTS conversation_tags (chat_id TEXT NOT NULL, tag_id INTEGER NOT NULL, PRIMARY KEY (chat_id, tag_id), FOREIGN KEY(tag_id) REFERENCES chat_tags(id) ON DELETE CASCADE)`);
        db.run(`CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT NOT NULL, contact_name TEXT, type TEXT NOT NULL, summary TEXT NOT NULL, timestamp INTEGER NOT NULL, is_read INTEGER NOT NULL DEFAULT 0)`);
        db.run(`CREATE TABLE IF NOT EXISTS Whatsapp_Queue_Local (id INTEGER PRIMARY KEY AUTOINCREMENT, task_type TEXT NOT NULL, related_id INTEGER NOT NULL, chat_id TEXT NOT NULL, message_body TEXT NOT NULL, scheduled_for INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending')`);

        console.log("✅ [1/4] Estructura de tablas base verificada.");

        // PASO 2: Limpiar tablas antiguas
        db.run(`DROP TABLE IF EXISTS Prompt_Modules`, () => {
            console.log("✅ [2/4] Tabla antigua de prompts eliminada (si existía).");
        });

        // PASO 3: Poblar datos por defecto
        db.run("INSERT OR IGNORE INTO chat_tags (name, color) VALUES ('Afiliado Verificado', '#28a745')");
        db.run("INSERT OR IGNORE INTO chat_tags (name, color) VALUES ('Nuevo Contacto', '#17a2b8')");

        const defaultSettings = {
            'model': 'gpt-4o',
            'prompt_new_user': 'PROMPT PARA USUARIOS NUEVOS VA AQUÍ.',
            'prompt_affiliate': 'PROMPT PARA AFILIADOS VA AQUÍ.'
        };
        const stmt = db.prepare("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)");
        for (const [key, value] of Object.entries(defaultSettings)) {
            stmt.run(key, value);
        }
        stmt.finalize((err) => {
            if (err) {
                console.error("❌ Error finalizando la configuración de settings:", err.message);
                return;
            }
            console.log("✅ [3/4] Datos por defecto verificados.");

            // PASO 4: Iniciar el servidor (ÚLTIMA ACCIÓN)
            console.log("✅ [4/4] Base de datos lista. Arrancando servidores...");
            startApp();
        });
    });
});

// =================================================================
// --- 3. FUNCIONES AUXILIARES ---
// =================================================================
async function callCrmTool(functionName, args) {
    const endpointMap = {
        'search_vacancies_tool': '/api/bot_tools/vacancies',
        'validate_registration_tool': '/api/bot_tools/validate_registration',
        'get_all_active_vacancies_tool': '/api/bot_tools/all_active_vacancies',
        'get_vacancy_details_tool': '/api/bot_tools/vacancy_details',
        'get_candidate_status_tool': '/api/bot_tools/candidate_status',
        'get_vacancies_with_details_tool': '/api/bot_tools/vacancies_with_details' // <<< NUEVA LÍNEA
    };
    const endpoint = endpointMap[functionName];
    if (!endpoint) throw new Error(`Herramienta desconocida: ${functionName}`);

    const params = new URLSearchParams(args);
    const url = `${process.env.CRM_API_URL}${endpoint}?${params.toString()}`;

    try {
        const response = await fetch(url, { headers: { 'X-API-Key': process.env.CRM_INTERNAL_API_KEY } });

        if (!response.ok) {
            const errorBody = await response.text();
            console.error(`Error en la API del CRM (${response.status}): ${errorBody}`);
            throw new Error(`Error en API CRM: ${response.statusText}`);
        }

        const responseText = await response.text();
        const responseData = responseText ? JSON.parse(responseText) : null;

        let recordCount = 0;
        if (responseData) {
            if (Array.isArray(responseData)) recordCount = responseData.length;
            else if (responseData.applications && Array.isArray(responseData.applications)) recordCount = responseData.applications.length;
            else recordCount = 1;
        }

        console.log(`\n--- Llamando Herramienta CRM: ${functionName} ---`);
        console.log(`URL: ${url}`);
        console.log(`-> Recibidos ${recordCount} registros de app.py.`);
        console.log(`--- FIN LLAMADA HERRAMIENTA ---\n`);

        return responseData;

    } catch (error) {
        console.error(`❌ FALLO DE CONEXIÓN con la herramienta CRM '${functionName}':`, error.message);
        return { error: `La herramienta ${functionName} falló al intentar contactar el servidor. Razón: ${error.message}` };
    }
}

async function analyzeConversationWithGemini(conversation) {
    if (!process.env.GEMINI_API_KEY) {
        console.warn("Advertencia: GEMINI_API_KEY no configurada. Se saltará el análisis.");
        return null;
    }

    const historyForAnalysis = conversation.map(msg => `${msg.from_me ? 'Asesor' : 'Usuario'}: ${msg.body}`).join('\n');

    const prompt = `
        Analiza la siguiente conversación de una agencia de empleos llamada Henmir.
        Responde ÚNICA Y EXCLUSIVAMENTE con un objeto JSON válido que empiece con '{' y termine con '}'. No incluyas texto, notas o marcadores de código antes o después del JSON.
        
        El objeto JSON debe tener estas claves:
        1. "sentiment": "positivo", "negativo" o "neutro".
        2. "topic": Clasifica el tema principal de la conversación. Elige UNO de los siguientes: "consulta_de_estado", "interes_en_vacante", "duda_sobre_pago", "problema_tecnico", "queja_general", "pregunta_frecuente", "despedida_o_cierre", "otro".
        3. "urgency": "alta", "media" o "baja".
        4. "summary": un resumen de máximo 10 palabras sobre la necesidad específica del usuario.

        CONVERSACIÓN:
        ---
        ${historyForAnalysis}
        ---
    `;

    try {
        console.log(`\n--- INICIANDO ANÁLISIS CON GEMINI ---`);
        console.log(`Enviando ${conversation.length} mensajes para análisis...`);

        const result = await geminiModel.generateContent(prompt);
        const response = await result.response;
        let text = response.text();

        const firstBracket = text.indexOf('{');
        const lastBracket = text.lastIndexOf('}');

        if (firstBracket === -1 || lastBracket === -1 || lastBracket < firstBracket) {
            throw new Error("La respuesta de Gemini no contenía un JSON válido.");
        }

        const jsonString = text.substring(firstBracket, lastBracket + 1);
        const jsonResponse = JSON.parse(jsonString);

        console.log(`Análisis de Gemini recibido:`);
        console.log(jsonResponse);
        console.log(`--- FIN DEL ANÁLISIS CON GEMINI ---\n`);

        return jsonResponse;

    } catch (error) {
        console.error("❌ Error analizando con Gemini:", error.message);
        return null;
    }
}

// --- ✨ NUEVO: MOTOR DE LA COLA DE MENSAJES (WHATSAPP WORKER) ✨ ---

const HONDURAS_TIMEZONE = 'America/Tegucigalpa';

// En bridge.js, reemplaza esta función completa
async function processMessageQueue() {
    // Verificar si hay alguna sesión activa
    const activeSessions = sessionManager.getAllSessions();
    if (activeSessions.length === 0) {
        return;
    }

    const now_utc_timestamp = Math.floor(Date.now() / 1000);
    const query = "SELECT * FROM Whatsapp_Queue_Local WHERE status = 'pending' AND scheduled_for <= ?";

    db.all(query, [now_utc_timestamp], async (err, tasks) => {
        if (err) {
            console.error("❌ Error al consultar la cola de mensajes:", err.message);
            return;
        }

        if (tasks.length === 0) {
            return;
        }

        console.log(`[Worker] Encontradas ${tasks.length} tareas pendientes. Procesando...`);

        for (const task of tasks) {
            db.run("UPDATE Whatsapp_Queue_Local SET status = 'processing' WHERE id = ?", [task.id]);

            // --- ✨ CORRECCIÓN Y LOG DE DIAGNÓSTICO ✨ ---
            // 1. Nos aseguramos de que el chat_id tenga el formato correcto.
            const formattedChatId = `${task.chat_id.replace(/@c\.us/g, '')}@c.us`;

            console.log(`[Worker] Intentando enviar Tarea #${task.id} a [${formattedChatId}]`);
            console.log(`[Worker] Contenido del Mensaje: "${task.message_body.substring(0, 80)}..."`);
            // --- FIN DE LA CORRECCIÓN ---

            try {
                // 2. Usamos el ID formateado para enviar el mensaje.
                await client.sendMessage(formattedChatId, task.message_body);

                console.log(`[Worker] ✅ Mensaje enviado a ${formattedChatId} para la tarea ${task.id}.`);

                if (task.task_type === 'postulation') {
                    await notifyBackendTaskStatus(task.related_id, 'sent');
                }

                db.run("DELETE FROM Whatsapp_Queue_Local WHERE id = ?", [task.id]);

            } catch (sendError) {
                console.error(`[Worker] ❌ Fallo al enviar mensaje para la tarea ${task.id}. Error: ${sendError.message}`);

                if (task.task_type === 'postulation') {
                    await notifyBackendTaskStatus(task.related_id, 'failed');
                }

                db.run("UPDATE Whatsapp_Queue_Local SET status = 'failed' WHERE id = ?", [task.id]);
            }
        }
    });
}

async function notifyBackendTaskStatus(postulationId, status) {
    try {
        const url = `${process.env.CRM_API_URL}/api/applications/update_notification_status`;
        await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': process.env.CRM_INTERNAL_API_KEY
            },
            body: JSON.stringify({ postulation_id: postulationId, status: status })
        });
        console.log(`[Worker] Notificado al backend: postulación ${postulationId} marcada como ${status}.`);
    } catch (apiError) {
        console.error(`[Worker] ❌ Fallo al notificar al backend para la postulación ${postulationId}. Error: ${apiError.message}`);
    }
}

// Iniciar el procesador de la cola para que se ejecute cada minuto
setInterval(processMessageQueue, 60 * 1000);

// --- FIN DEL NUEVO BLOQUE ---

/**
 * Genera una respuesta de la IA basada en un estado específico y el historial de chat.
 * @param {string} state - El module_id del estado para el que se generará la respuesta (ej. 'AWAITING_CITY').
 * @param {string} chatId - El ID del chat.
 * @param {string} userMessage - El último mensaje del usuario para el contexto.
 * @returns {Promise<string>} La respuesta de texto generada por la IA.
 */
async function generateResponseForState(state, chatId, userMessage) {
    console.log(`[Text Gen] Generando respuesta para el nuevo estado: ${state}`);

    // 1. Cargar el módulo de prompt para el nuevo estado
    const module = await new Promise((resolve, reject) => {
        db.get("SELECT * FROM Prompt_Modules WHERE module_id = ?", [state], (err, row) => {
            if (err) return reject(new Error(`Error de BD al cargar módulo para ${state}.`));
            if (!row) return reject(new Error(`Módulo '${state}' no definido.`));
            resolve(row);
        });
    });

    // 2. Cargar las bases de conocimiento asociadas (si las tiene)
    const kbAccessIds = JSON.parse(module.knowledge_base_access || '[]');
    let knowledgeBaseContent = "";
    if (kbAccessIds.length > 0) {
        const placeholders = kbAccessIds.map(() => '?').join(',');
        const kbModules = await new Promise((resolve, reject) => {
            db.all(`SELECT module_name, instructions FROM Prompt_Modules WHERE module_id IN (${placeholders})`, kbAccessIds, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
        knowledgeBaseContent = kbModules.map(kb => `### ${kb.module_name}\n${kb.instructions}`).join('\n\n');
    }

    // 3. Ensamblar un prompt de sistema enfocado únicamente en generar el texto de inicio para el nuevo estado
    let systemPrompt = `--- ROL Y MISIÓN PRINCIPAL ---\nROL: ${module.role}\nMISIÓN: ${module.mission}\nINSTRUCCIONES: ${module.instructions}\n--- FIN ROL Y MISIÓN PRINCIPAL ---`;
    if (knowledgeBaseContent) {
        systemPrompt += `\n\n--- BASE DE CONOCIMIENTO ADICIONAL ---\n${knowledgeBaseContent}\n--- FIN BASE DE CONOCIMIENTO ---`;
    }
    systemPrompt += "\n\nTAREA ACTUAL: Basado en tus instrucciones, genera la primera respuesta o pregunta para iniciar esta etapa de la conversación. Sé directo y sigue tus instrucciones al pie de la letra.";

    // 4. Preparar una llamada a la IA muy simple, sin historial complejo ni herramientas, solo para generar texto.
    const messages = [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: `El usuario acaba de decir: "${userMessage}". Ahora inicia tu parte de la conversación.` }
    ];

    const response = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: messages,
    });

    const generatedText = response.choices[0].message.content;
    console.log(`[Text Gen] Respuesta generada para ${state}: "${generatedText.substring(0, 50)}..."`);
    return generatedText;
}
// =================================================================
// --- 4. RUTAS DE LA API HTTP (EXPRESS) ---
// =================================================================

/**
 * @api {post} /api/session/init Inicializar una nueva sesión
 * @apiName InitSession
 * @apiGroup Session
 * 
 * @apiBody {String} session_id Identificador único de la sesión
 * @apiBody {String} [tenant_id=default] Identificador del tenant (opcional)
 * 
 * @apiSuccess {String} sessionId ID de la sesión
 * @apiSuccess {String} status Estado de la sesión
 * @apiSuccess {String} message Mensaje descriptivo
 */
app.post('/api/session/init', async (req, res) => {
    try {
        const { session_id: sessionId, tenant_id: tenantId = 'default' } = req.body;

        if (!sessionId) {
            return res.status(400).json({
                error: 'Se requiere el parámetro session_id',
            });
        }

        const result = await startSession(sessionId, tenantId);
        res.json(result);

    } catch (error) {
        console.error('Error al inicializar la sesión:', error);
        res.status(500).json({
            error: 'Error al inicializar la sesión',
            details: error.message,
        });
    }
});

/**
 * @api {post} /api/session/:sessionId/message Enviar un mensaje a través de una sesión
 * @apiName SendMessage
 * @apiGroup Session
 * 
 * @apiParam {String} sessionId ID de la sesión
 * @apiBody {String} chatId ID del chat de WhatsApp (número de teléfono con @c.us)
 * @apiBody {String} message Contenido del mensaje a enviar
 * 
 * @apiSuccess {String} status Estado de la operación
 * @apiSuccess {String} messageId ID del mensaje enviado
 */
app.post('/api/session/:sessionId/message', async (req, res) => {
    try {
        const { sessionId } = req.params;
        const { chatId, message } = req.body;

        if (!chatId || !message) {
            return res.status(400).json({
                error: 'Se requieren los parámetros chatId y message'
            });
        }

        const result = await sendMessageToSession(sessionId, chatId, message);
        res.json(result);

    } catch (error) {
        console.error('Error al enviar mensaje:', error);
        res.status(500).json({
            error: 'Error al enviar el mensaje',
            details: error.message
        });
    }
});

/**
 * @api {get} /api/session/:sessionId/status Obtener el estado de una sesión
 * @apiName GetSessionStatus
 * @apiGroup Session
 * 
 * @apiParam {String} sessionId ID de la sesión
 * 
 * @apiSuccess {String} sessionId ID de la sesión
 * @apiSuccess {String} status Estado actual de la sesión
 * @apiSuccess {String} proxy Proxy en uso (si aplica)
 * @apiSuccess {String} tenantId ID del tenant
 * @apiSuccess {String} lastActivity Última actividad
 */
app.get('/api/session/:sessionId/status', (req, res) => {
    const { sessionId } = req.params;
    const session = activeSessions.get(sessionId);

    if (!session) {
        return res.status(404).json({
            error: 'Sesión no encontrada'
        });
    }

    res.json({
        sessionId,
        status: session.status,
        proxy: session.proxy,
        tenantId: session.tenantId,
        lastActivity: session.lastActivity.toISOString(),
        isReady: session.status === 'ready'
    });
});

/**
 * @api {get} /api/sessions Listar todas las sesiones activas
 * @apiName ListSessions
 * @apiGroup Session
 * 
 * @apiSuccess {Object[]} sessions Lista de sesiones activas
 */
app.get('/api/sessions', (req, res) => {
    const sessions = Array.from(activeSessions.entries()).map(([sessionId, session]) => ({
        sessionId,
        status: session.status,
        proxy: session.proxy,
        tenantId: session.tenantId,
        lastActivity: session.lastActivity.toISOString(),
        isReady: session.status === 'ready'
    }));

    res.json({ sessions });
});

/**
 * @api {delete} /api/session/:sessionId Cerrar una sesión
 * @apiName CloseSession
 * @apiGroup Session
 * 
 * @apiParam {String} sessionId ID de la sesión a cerrar
 */
app.delete('/api/session/:sessionId', async (req, res) => {
    try {
        const { sessionId } = req.params;
        await cleanupSession(sessionId);
        res.json({ success: true, message: 'Sesión cerrada correctamente' });
    } catch (error) {
        console.error('Error al cerrar la sesión:', error);
        res.status(500).json({
            error: 'Error al cerrar la sesión',
            details: error.message
        });
    }
});

/**
 * Envía un mensaje a través de una sesión específica
 * @param {string} sessionId - ID de la sesión
 * @param {string} chatId - ID del chat de WhatsApp
 * @param {string} message - Contenido del mensaje
 * @returns {Promise<Object>} Resultado de la operación
 */
async function sendMessageToSession(sessionId, chatId, message) {
    const session = activeSessions.get(sessionId);

    if (!session) {
        throw new Error(`No se encontró una sesión activa con ID: ${sessionId}`);
    }

    if (session.status !== 'ready') {
        throw new Error(`La sesión no está lista. Estado actual: ${session.status}`);
    }

    try {
        // Verificar si el chatId tiene el formato correcto
        const formattedChatId = chatId.endsWith('@c.us') ? chatId : `${chatId}@c.us`;

        // Enviar el mensaje
        const sentMessage = await session.client.sendMessage(formattedChatId, message);

        // Actualizar la última actividad
        session.lastActivity = new Date();

        // Registrar el mensaje en la base de datos
        await new Promise((resolve, reject) => {
            db.run(
                'INSERT INTO messages (chat_id, sender, body, timestamp, from_me) VALUES (?, ?, ?, ?, ?)',
                [formattedChatId, 'me', message, Math.floor(Date.now() / 1000), true],
                (err) => err ? reject(err) : resolve()
            );
        });

        // Actualizar la conversación
        await new Promise((resolve, reject) => {
            db.run(
                'INSERT OR REPLACE INTO conversations (chat_id, last_message_timestamp) VALUES (?, ?)',
                [formattedChatId, Math.floor(Date.now() / 1000)],
                (err) => err ? reject(err) : resolve()
            );
        });

        return {
            success: true,
            messageId: sentMessage.id.id,
            timestamp: new Date().toISOString()
        };

    } catch (error) {
        console.error(`[${sessionId}] Error al enviar mensaje a ${chatId}:`, error);
        throw new Error(`Error al enviar mensaje: ${error.message}`);
    }
}

/**
 * Notifica la recepción de un nuevo mensaje a través del WebSocket
 * @param {string} sessionId - ID de la sesión
 * @param {Object} message - Objeto de mensaje de WhatsApp
 */
function notifyNewMessage(sessionId, message) {
    const session = activeSessions.get(sessionId);
    if (!session) return;

    const messageData = {
        type: 'new_message',
        sessionId,
        messageId: message.id.id,
        chatId: message.from,
        fromMe: message.fromMe,
        body: message.body,
        timestamp: message.timestamp,
        hasMedia: message.hasMedia,
        status: message.ack
    };

    // Enviar a través del WebSocket si está disponible
    if (crmSocket && crmSocket.readyState === WebSocket.OPEN) {
        crmSocket.send(JSON.stringify(messageData));
    }
}




app.get('/api/crm/chatbot-settings', (req, res) => {
    db.all("SELECT key, value FROM settings WHERE key IN ('model', 'prompt_new_user', 'prompt_affiliate')", [], (err, rows) => {
        if (err) {
            console.error("Error al obtener ajustes del chatbot desde DB:", err);
            return res.status(500).json({ error: "Error de base de datos" });
        }
        const settings = rows.reduce((acc, row) => ({ ...acc, [row.key]: row.value }), {});
        res.json(settings);
    });
});

app.post('/api/crm/chatbot-settings', (req, res) => {
    const { model, prompt_new_user, prompt_affiliate } = req.body;

    if (model === undefined || prompt_new_user === undefined || prompt_affiliate === undefined) {
        return res.status(400).json({ error: "Faltan datos clave (model, prompt_new_user, prompt_affiliate)" });
    }

    db.serialize(() => {
        const stmt = db.prepare("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)");
        stmt.run('model', model);
        stmt.run('prompt_new_user', prompt_new_user);
        stmt.run('prompt_affiliate', prompt_affiliate);
        stmt.finalize((err) => {
            if (err) {
                console.error("Error al guardar ajustes en DB:", err);
                return res.status(500).json({ error: "No se pudo guardar." });
            }
            res.json({ message: "Configuración guardada exitosamente." });
        });
    });
});
// Endpoint para obtener la lista de todos los módulos para el menú
app.get('/api/crm/prompt-modules', (req, res) => {
    const query = "SELECT module_id, module_name, is_knowledge_base FROM Prompt_Modules ORDER BY module_name";
    db.all(query, [], (err, rows) => {
        if (err) {
            console.error("Error al obtener lista de módulos de prompt:", err);
            return res.status(500).json({ error: "Error de base de datos" });
        }
        res.json(rows);
    });
});

// Endpoint para obtener los detalles completos de un módulo específico
app.get('/api/crm/prompt-modules/:moduleId', (req, res) => {
    const { moduleId } = req.params;
    const query = "SELECT * FROM Prompt_Modules WHERE module_id = ?";
    db.get(query, [moduleId], (err, row) => {
        if (err) {
            console.error(`Error al obtener detalles del módulo ${moduleId}:`, err);
            return res.status(500).json({ error: "Error de base de datos" });
        }
        if (!row) {
            return res.status(404).json({ error: "Módulo de prompt no encontrado." });
        }
        // Parseamos los campos JSON antes de enviarlos
        try {
            row.tools_allowed = JSON.parse(row.tools_allowed || '[]');
            row.knowledge_base_access = JSON.parse(row.knowledge_base_access || '[]');
        } catch (e) {
            console.error("Error parseando JSON de la BD:", e);
            // Devolver valores por defecto si el parseo falla
            row.tools_allowed = [];
            row.knowledge_base_access = [];
        }
        res.json(row);
    });
});

// Endpoint para actualizar un módulo de prompt
app.put('/api/crm/prompt-modules/:moduleId', (req, res) => {
    const { moduleId } = req.params;
    const { role, mission, instructions, tools_allowed, knowledge_base_access } = req.body;

    // Validación de entrada
    if (role === undefined || mission === undefined || instructions === undefined || !Array.isArray(tools_allowed) || !Array.isArray(knowledge_base_access)) {
        return res.status(400).json({ error: "Faltan campos o los campos de array no son válidos." });
    }

    const query = `
        UPDATE Prompt_Modules SET
            role = ?,
            mission = ?,
            instructions = ?,
            tools_allowed = ?,
            knowledge_base_access = ?
        WHERE module_id = ?
    `;

    const params = [
        role,
        mission,
        instructions,
        JSON.stringify(tools_allowed),
        JSON.stringify(knowledge_base_access),
        moduleId
    ];

    db.run(query, params, function (err) {
        if (err) {
            console.error(`Error al actualizar el módulo ${moduleId}:`, err);
            return res.status(500).json({ error: "Error de base de datos al guardar." });
        }
        if (this.changes === 0) {
            return res.status(404).json({ error: "Módulo de prompt no encontrado para actualizar." });
        }
        res.json({ success: true, message: "Módulo de prompt guardado exitosamente." });
    });
});


app.post('/api/whatsauto_reply', async (req, res) => {
    const { sender, message } = req.body;
    if (!sender || !message) return res.status(400).json({ error: "Faltan datos" });
    if (['📷', 'Fotografía', 'image/'].some(p => message.includes(p))) return res.json({ reply: "" });

    const chatId = `${sender.replace(/\D/g, '')}@c.us`;

    try {
        const userState = await new Promise((resolve, reject) => {
            db.get('SELECT * FROM conversations WHERE chat_id = ?', [chatId], (err, row) => {
                if (err) return reject(new Error("Error de DB al obtener estado."));
                if (!row) return reject(new Error("Conversación no encontrada."));
                resolve(row);
            });
        });

        if (userState.bot_active === 0) return res.json({ reply: "" });

        const settings = await new Promise((resolve, reject) => {
            db.all("SELECT key, value FROM settings", (err, rows) => {
                if (err) return reject(new Error("No se pudo cargar la configuración."));
                resolve(rows.reduce((acc, row) => ({ ...acc, [row.key]: row.value }), {}));
            });
        });

        const promptKey = userState.status === 'identified_affiliate' || userState.status === 'AFFILIATE_LOGGED_IN' ? 'prompt_affiliate' : 'prompt_new_user';
        const systemPrompt = settings[promptKey];
        const model = settings.model || 'gpt-4o';

        const historyFromDb = await new Promise((resolve, reject) => {
            db.all("SELECT from_me, body FROM messages WHERE chat_id = ? ORDER BY timestamp DESC LIMIT 8", [chatId], (err, rows) => err ? reject(err) : resolve(rows.reverse()));
        });
        const formattedHistory = historyFromDb.map(msg => ({ role: msg.from_me ? 'assistant' : 'user', content: msg.body }));

        const messagesForOpenAI = [
            { role: 'system', content: systemPrompt },
            ...formattedHistory,
            {
                role: 'user',
                content: `--- INICIO DE CONTEXTO DE SISTEMA ---\n${JSON.stringify(userState, null, 2)}\n--- FIN DE CONTEXTO DE SISTEMA ---\n\nMENSAJE_DEL_USUARIO: "${message}"`
            }
        ];

        const available_tools = [
            { type: "function", function: { name: "search_vacancies_tool", description: "Busca vacantes disponibles en una ciudad específica, opcionalmente filtrando por una palabra clave o área.", parameters: { type: "object", properties: { city: { type: "string", description: "La ciudad donde buscar las vacantes, ej: 'San Pedro Sula'" }, keyword: { type: "string", description: "Una palabra clave para filtrar, ej: 'ventas', 'cocinero'" } }, required: ["city"] } } },
            { type: "function", function: { name: "validate_registration_tool", description: "Valida si un número de identidad ya está registrado en el sistema de afiliados.", parameters: { type: "object", properties: { identity: { type: "string", description: "El número de identidad del usuario, sin guiones ni espacios." } }, required: ["identity"] } } },

            // ✨ CORRECCIÓN CLAVE #1 AQUÍ ✨
            // El parámetro ahora se llama 'cargo_solicitado' para coincidir con lo que espera app.py
            { type: "function", function: { name: "get_vacancy_details_tool", description: "Obtiene los detalles y requisitos de una vacante específica por su nombre.", parameters: { type: "object", properties: { cargo_solicitado: { type: "string" } }, required: ["cargo_solicitado"] } } },

            { type: "function", function: { name: "get_candidate_status_tool", description: "Consulta el estado actual de las postulaciones de un candidato usando su número de identidad.", parameters: { type: "object", properties: { identity_number: { type: "string", description: "El número de identidad del afiliado, sin guiones ni espacios." } }, required: ["identity_number"] } } }
        ];

        const initialResponse = await openai.chat.completions.create({ model: model, messages: messagesForOpenAI, tools: available_tools, tool_choice: "auto" });

        const responseMessage = initialResponse.choices[0].message;
        let finalReply = responseMessage.content || "";
        let nextState = userState.status;

        const toolCalls = responseMessage.tool_calls;
        if (toolCalls) {
            messagesForOpenAI.push(responseMessage);

            for (const toolCall of toolCalls) {
                const functionName = toolCall.function.name;
                const functionArgs = JSON.parse(toolCall.function.arguments);

                console.log(`[Tool Call] La IA solicita ejecutar '${functionName}' con args:`, functionArgs);
                const toolResult = await callCrmTool(functionName, functionArgs);

                if (functionArgs.city) db.run("UPDATE conversations SET context_city = ? WHERE chat_id = ?", [functionArgs.city.trim(), chatId]);
                if (functionArgs.area) db.run("UPDATE conversations SET context_area = ? WHERE chat_id = ?", [functionArgs.area.trim(), chatId]);

                if (functionName === 'validate_registration_tool') {
                    if (toolResult && toolResult.success === true) {
                        nextState = 'AFFILIATE_LOGGED_IN';
                        db.run("UPDATE conversations SET known_identity = ?, status = ?, chat_type = 'candidate' WHERE chat_id = ?", [functionArgs.identity, nextState, chatId]);
                    } else {
                        nextState = 'VALIDATION_FAILED';
                        db.run("UPDATE conversations SET status = ? WHERE chat_id = ?", [nextState, chatId]);
                    }
                }

                messagesForOpenAI.push({ tool_call_id: toolCall.id, role: "tool", name: functionName, content: JSON.stringify(toolResult) });
            }

            const secondResponse = await openai.chat.completions.create({ model: model, messages: messagesForOpenAI });
            finalReply = secondResponse.choices[0].message.content;
        }

        if (nextState !== userState.status) {
            console.log(`[State Transition] Chat: ${chatId} | De: ${userState.status} -> A: ${nextState}`);
        }

        if (finalReply) {
            const responseTime = Math.floor(Date.now() / 1000);
            db.run(`INSERT INTO messages (chat_id, sender, body, timestamp, from_me) VALUES (?, ?, ?, ?, ?)`, [chatId, 'me', finalReply, responseTime, true]);
            db.run(`UPDATE conversations SET last_message_timestamp = ? WHERE chat_id = ?`, [responseTime, chatId]);
        }

        return res.json({ reply: finalReply });

    } catch (error) {
        console.error(`❌ Error fatal en el flujo para ${chatId}:`, error);
        return res.json({ reply: "Lo siento, tengo un problema técnico. Un asesor revisará su caso." });
    }
});


app.get('/api/crm/chats', async (req, res) => {
    // ✨ CONSULTA MEJORADA: Ahora selecciona 'is_pinned' y 'unread_count'
    // y ordena por 'is_pinned' DESC para que los anclados salgan primero.
    const query = `
        SELECT 
            c.*,
            c.chat_id as id, 
            c.contact_name as name, 
            (SELECT body FROM messages WHERE chat_id = c.chat_id ORDER BY timestamp DESC LIMIT 1) as lastMessage,
            (SELECT from_me FROM messages WHERE chat_id = c.chat_id ORDER BY timestamp DESC LIMIT 1) as lastMessageFromMe,
            (SELECT GROUP_CONCAT(json_object('id', T.id, 'name', T.name, 'color', T.color)) 
             FROM chat_tags T
             JOIN conversation_tags CT ON T.id = CT.tag_id
             WHERE CT.chat_id = c.chat_id) as tags
        FROM conversations c 
        WHERE c.last_message_timestamp IS NOT NULL 
        ORDER BY c.is_pinned DESC, c.last_message_timestamp DESC 
        LIMIT 200;
    `;

    db.all(query, [], (err, rows) => {
        if (err) {
            console.error("Error al obtener chats para la lista:", err);
            return res.status(500).json({ error: "Error de base de datos al cargar los chats." });
        }

        const finalRows = rows.map(row => ({
            ...row,
            lastMessage: row.lastMessage ? row.lastMessage.slice(0, 50) : '[Mensaje multimedia]',
            lastMessageFromMe: !!row.lastMessageFromMe,
            tags: row.tags ? JSON.parse(`[${row.tags}]`) : []
        }));

        res.json(finalRows);
    });
});



app.get('/api/crm/conversations/:chatId', (req, res) => {
    const { chatId } = req.params;

    // Usamos Promise.all para ejecutar todas las consultas en paralelo, es más eficiente.
    Promise.all([
        // Consulta 1: Mensajes
        new Promise((resolve, reject) => {
            db.all(`SELECT * FROM messages WHERE chat_id = ? ORDER BY timestamp ASC`, [chatId], (err, rows) => {
                if (err) return reject(err);
                resolve(rows || []); // Siempre devolver un array, aunque esté vacío
            });
        }),
        // Consulta 2: Datos de la conversación
        new Promise((resolve, reject) => {
            db.get(`SELECT * FROM conversations WHERE chat_id = ?`, [chatId], (err, row) => {
                if (err) return reject(err);
                // Si no hay datos, devolver un objeto por defecto para evitar errores en el frontend
                resolve(row || { bot_active: 1, custom_name: null, chat_type: 'unassigned', contact_name: chatId.split('@')[0], status: 'new_visitor', known_identity: null });
            });
        }),
        // Consulta 3: Etiquetas
        new Promise((resolve, reject) => {
            db.all(`
                SELECT T.id, T.name, T.color 
                FROM chat_tags T
                JOIN conversation_tags CT ON T.id = CT.tag_id
                WHERE CT.chat_id = ?`, [chatId], (err, rows) => {
                if (err) return reject(err);
                resolve(rows || []); // Siempre devolver un array
            });
        })
    ]).then(([messages, conversation, tags]) => {
        // Si todo tiene éxito, construimos y enviamos el objeto de respuesta completo
        res.json({
            messages: messages,
            bot_active: conversation.bot_active,
            custom_name: conversation.custom_name,
            chat_type: conversation.chat_type,
            contact_name: conversation.contact_name,
            status: conversation.status,
            known_identity: conversation.known_identity,
            tags: tags
        });
    }).catch(error => {
        // Si CUALQUIERA de las promesas falla, capturamos el error aquí
        console.error(`❌ Error fatal obteniendo datos de conversación para ${chatId}:`, error.message);
        res.status(500).json({ error: "Error de base de datos al cargar la conversación." });
    });
});



app.post('/api/crm/chats/:chatId/context', (req, res) => {
    const { chatId } = req.params;
    const { custom_name, chat_type } = req.body;

    if (!custom_name && !chat_type) {
        return res.status(400).json({ error: 'Se requiere al menos un campo para actualizar.' });
    }

    const sql = `
        UPDATE conversations 
        SET 
            custom_name = COALESCE(?, custom_name),
            chat_type = COALESCE(?, chat_type)
        WHERE chat_id = ?
    `;

    db.run(sql, [custom_name || null, chat_type || null, chatId], function (err) {
        if (err) {
            console.error("Error actualizando contexto de chat:", err.message);
            return res.status(500).json({ error: err.message });
        }
        if (this.changes === 0) return res.status(404).json({ error: 'Chat no encontrado.' });
        res.json({ success: true, message: 'Contexto del chat actualizado.' });
    });
});




// --- ENDPOINTS PARA GESTIONAR LAS ETIQUETAS DE CHAT (CRUD) ---

// Obtener todas las etiquetas disponibles
app.get('/api/crm/chattags', (req, res) => {
    db.all("SELECT * FROM chat_tags ORDER BY name ASC", [], (err, rows) => {
        if (err) return res.status(500).json({ error: "Error de base de datos" });
        res.json(rows);
    });
});

// Crear una nueva etiqueta
app.post('/api/crm/chattags', (req, res) => {
    const { name, color } = req.body;
    if (!name) return res.status(400).json({ error: "El nombre es requerido" });
    db.run("INSERT INTO chat_tags (name, color) VALUES (?, ?)", [name, color || '#808080'], function (err) {
        if (err) return res.status(500).json({ error: err.message });
        res.status(201).json({ id: this.lastID, name, color });
    });
});

// Asignar una etiqueta a un chat
app.post('/api/crm/chats/:chatId/tags', (req, res) => {
    const { chatId } = req.params;
    const { tag_id } = req.body;
    if (!tag_id) return res.status(400).json({ error: "Se requiere tag_id" });

    db.run("INSERT INTO conversation_tags (chat_id, tag_id) VALUES (?, ?)", [chatId, tag_id], (err) => {
        if (err) {
            // Ignoramos el error si la etiqueta ya estaba asignada (PRIMARY KEY constraint)
            if (err.message.includes('UNIQUE constraint failed')) {
                return res.json({ success: true, message: "La etiqueta ya estaba asignada." });
            }
            return res.status(500).json({ error: err.message });
        }
        res.status(201).json({ success: true, message: "Etiqueta asignada." });
    });
});

// Remover una etiqueta de un chat
app.delete('/api/crm/chats/:chatId/tags/:tagId', (req, res) => {
    const { chatId, tagId } = req.params;
    db.run("DELETE FROM conversation_tags WHERE chat_id = ? AND tag_id = ?", [chatId, tagId], function (err) {
        if (err) return res.status(500).json({ error: err.message });
        if (this.changes === 0) return res.status(404).json({ error: "Asignación de etiqueta no encontrada." });
        res.json({ success: true, message: "Etiqueta removida." });
    });
});


// =================================================================
app.get('/api/crm/notifications', (req, res) => {
    const query = "SELECT * FROM notifications WHERE is_read = 0 ORDER BY timestamp DESC";
    db.all(query, [], (err, rows) => {
        if (err) return res.status(500).json({ error: "Error de base de datos" });
        res.json(rows);
    });
});

app.post('/api/crm/notifications/:id/mark-read', (req, res) => {
    const { id } = req.params;
    const query = "UPDATE notifications SET is_read = 1 WHERE id = ?";
    db.run(query, [id], function (err) {
        if (err) return res.status(500).json({ error: "Error de base de datos" });
        if (this.changes === 0) return res.status(404).json({ error: "Notificación no encontrada." });
        res.json({ success: true, message: "Notificación marcada como leída." });
    });
});




app.post('/api/crm/chats/:chatId/manual_status', async (req, res) => {
    const { chatId } = req.params;
    const { new_status, identity_number } = req.body;

    // Validación rigurosa de la entrada
    if (!new_status || (new_status !== 'identified_affiliate' && new_status !== 'new_visitor')) {
        return res.status(400).json({ error: "El campo 'new_status' es inválido o está ausente." });
    }
    if (new_status === 'identified_affiliate' && (!identity_number || identity_number.trim() === '')) {
        return res.status(400).json({ error: 'Se requiere un número de identidad para el estado de afiliado.' });
    }

    try {
        // Usamos una transacción para garantizar la atomicidad de la operación
        await new Promise((resolve, reject) => db.run('BEGIN TRANSACTION', err => err ? reject(err) : resolve()));

        // 1. Actualizar el estado y la identidad en la tabla 'conversations'
        const clean_identity = new_status === 'identified_affiliate' ? identity_number.trim() : null;
        const chat_type = new_status === 'identified_affiliate' ? 'candidate' : 'unassigned';

        await new Promise((resolve, reject) => {
            db.run(
                `UPDATE conversations SET status = ?, known_identity = ?, chat_type = ? WHERE chat_id = ?`,
                [new_status, clean_identity, chat_type, chatId],
                function (err) {
                    if (err) return reject(err);
                    if (this.changes === 0) return reject(new Error('Chat no encontrado para actualizar.'));
                    resolve();
                }
            );
        });

        // 2. Gestionar las etiquetas de estado de forma inteligente
        const affiliateTagName = 'Afiliado Verificado';
        const newContactTagName = 'Nuevo Contacto';

        // Obtener los IDs de ambas etiquetas de estado
        const tags = await new Promise((resolve, reject) => {
            db.all("SELECT id, name FROM chat_tags WHERE name IN (?, ?)", [affiliateTagName, newContactTagName], (err, rows) => {
                if (err) return reject(err);
                resolve(rows.reduce((acc, row) => ({ ...acc, [row.name]: row.id }), {}));
            });
        });

        const affiliateTagId = tags[affiliateTagName];
        const newContactTagId = tags[newContactTagName];

        if (!affiliateTagId || !newContactTagId) {
            throw new Error("Las etiquetas de estado base ('Afiliado Verificado', 'Nuevo Contacto') no existen en la base de datos.");
        }

        // Eliminar AMBAS etiquetas de estado para limpiar antes de asignar la correcta
        await new Promise((resolve, reject) => {
            db.run(`DELETE FROM conversation_tags WHERE chat_id = ? AND tag_id IN (?, ?)`,
                [chatId, affiliateTagId, newContactTagId],
                err => err ? reject(err) : resolve());
        });

        // Asignar la etiqueta correcta según el nuevo estado
        const tagIdToAssign = new_status === 'identified_affiliate' ? affiliateTagId : newContactTagId;
        await new Promise((resolve, reject) => {
            db.run("INSERT OR IGNORE INTO conversation_tags (chat_id, tag_id) VALUES (?, ?)",
                [chatId, tagIdToAssign],
                err => err ? reject(err) : resolve());
        });

        // Si todo fue bien, confirmamos los cambios
        await new Promise((resolve, reject) => db.run('COMMIT', err => err ? reject(err) : resolve()));

        console.log(`[Manual Flow Change] Flujo cambiado a '${new_status}' para el chat ${chatId}.`);
        res.json({ success: true, message: 'El flujo del usuario ha sido actualizado manualmente.' });

    } catch (error) {
        // Si algo falla, revertimos todos los cambios para no dejar la BD en un estado inconsistente
        await new Promise(resolve => db.run('ROLLBACK', () => resolve()));
        console.error("Error en la actualización manual de flujo:", error.message);
        res.status(500).json({ error: error.message || 'Error de base de datos al actualizar el flujo.' });
    }
});

app.post('/api/crm/internal/run_initial_sync', async (req, res) => {
    console.log("=====================================================");
    console.log("🚀 INICIANDO SINCRONIZACIÓN MASIVA NO DESTRUCTIVA 🚀");
    console.log("=====================================================");

    try {
        // 1. Obtener la etiqueta 'Afiliado Verificado' de nuestra BD local
        const tag = await new Promise((resolve, reject) => {
            db.get("SELECT id FROM chat_tags WHERE name = 'Afiliado Verificado'", (err, row) => {
                if (err) return reject(new Error("Error de BD al buscar la etiqueta."));
                if (!row) return reject(new Error("La etiqueta 'Afiliado Verificado' no existe. Asegúrate de que el servidor la haya creado."));
                resolve(row);
            });
        });
        const affiliateTagId = tag.id;

        // 2. Obtener la lista completa de afiliados desde el CRM principal (app.py)
        const affiliatesResponse = await fetch(`${process.env.CRM_API_URL}/api/internal/all_affiliates_for_sync`, {
            headers: { 'X-API-Key': process.env.CRM_INTERNAL_API_KEY }
        });

        if (!affiliatesResponse.ok) {
            throw new Error(`El servidor CRM respondió con error: ${affiliatesResponse.status}`);
        }
        const affiliates = await affiliatesResponse.json();
        console.log(`[Sync] Recibidos ${affiliates.length} afiliados desde el CRM principal para procesar.`);

        let processedCount = 0;

        // 3. Usar una transacción para hacer el proceso más eficiente y seguro
        await new Promise(resolve => db.run('BEGIN TRANSACTION', resolve));

        // LÍNEA NUEVA Y CORRECTA
        const upsertStmt = db.prepare(
            `INSERT INTO conversations (chat_id, contact_name, status, known_identity, chat_type)
            VALUES (?, ?, 'AFFILIATE_LOGGED_IN', ?, 'candidate')
            ON CONFLICT(chat_id) DO UPDATE SET
               status = excluded.status,
               known_identity = excluded.known_identity,
               chat_type = excluded.chat_type;`
        );

        // Sentencia preparada para asignar la etiqueta
        const tagStmt = db.prepare(
            `INSERT OR IGNORE INTO conversation_tags (chat_id, tag_id) VALUES (?, ?)`
        );

        for (const affiliate of affiliates) {
            if (!affiliate.telefono || !affiliate.identidad) continue;

            const chatId = `${affiliate.telefono}@c.us`;
            const identity = affiliate.identidad.replace(/-/g, '').trim();
            const contactName = `Afiliado ${identity.slice(-4)}`; // Un nombre por defecto si no hay conversación

            // Ejecutar el UPSERT para la conversación
            upsertStmt.run(chatId, contactName, identity);
            // Asignar la etiqueta de afiliado
            tagStmt.run(chatId, affiliateTagId);

            processedCount++;
        }

        // Finalizar las sentencias preparadas y la transacción
        await new Promise(resolve => upsertStmt.finalize(resolve));
        await new Promise(resolve => tagStmt.finalize(resolve));
        await new Promise(resolve => db.run('COMMIT', resolve));

        const summaryMessage = `Sincronización completada. ${processedCount} registros de afiliados procesados. Los historiales de chat existentes se han conservado y actualizado.`;
        console.log(summaryMessage);
        res.json({ success: true, message: summaryMessage });

    } catch (error) {
        // En caso de CUALQUIERA de los errores, revertir todos los cambios para no dejar la BD en un estado inconsistente
        await new Promise(resolve => db.run('ROLLBACK', () => resolve()));
        console.error("❌ ERROR FATAL durante la sincronización:", error.message);
        res.status(500).json({ success: false, error: error.message });
    }
});


app.get('/api/crm/chat_context/:identityNumber', async (req, res) => {
    const { identityNumber } = req.params;
    if (!identityNumber) {
        return res.status(400).json({ error: "Número de identidad es requerido." });
    }

    console.log(`[Contexto] Solicitando contexto del CRM para la identidad: ${identityNumber}`);

    try {
        const crmUrl = `${process.env.CRM_API_URL}/api/internal/chat_context/${identityNumber}`;
        const crmResponse = await fetch(crmUrl, {
            headers: { 'X-API-Key': process.env.CRM_INTERNAL_API_KEY }
        });

        const responseData = await crmResponse.json();

        if (!crmResponse.ok) {
            // Pasamos el error del backend principal al frontend
            return res.status(crmResponse.status).json(responseData);
        }

        res.json(responseData);

    } catch (error) {
        console.error(`[Contexto] Error fatal obteniendo contexto para ${identityNumber}:`, error.message);
        res.status(500).json({ error: "Error de conexión con el servidor principal del CRM." });
    }
});



app.post('/api/crm/suggest_reply', async (req, res) => {
    // ✨ CORRECCIÓN: Se eliminó la sintaxis de TypeScript ": any".
    const { history, current_text } = req.body;

    // Validación de la entrada
    if (!Array.isArray(history)) {
        return res.status(400).json({ error: "El historial debe ser un array." });
    }

    try {
        const formattedHistory = history.map(msg => `${msg.from_me ? 'Reclutador' : 'Usuario'}: ${msg.body}`).join('\n');

        const systemPrompt = `
            Eres un asistente de IA para un reclutador de la agencia Henmir. Tu única función es autocompletar texto.
            Analiza el historial de la conversación y el texto que el reclutador está escribiendo.
            Tu objetivo es predecir las siguientes 2 a 5 palabras que el reclutador probablemente escribiría.

            ### REGLAS CRÍTICAS E INQUEBRANTABLES ###
            1.  **SOLO AUTOCOMPLETAR:** Tu respuesta debe ser la continuación DIRECTA de la frase del reclutador. NO generes una frase nueva y completa si el reclutador ya empezó a escribir.
            2.  **EXTREMA BREVEDAD:** Tu sugerencia debe ser muy corta, idealmente entre 2 y 5 palabras. NUNCA una oración larga.
            3.  **RESPUESTA LIMPIA:** Tu salida debe ser ÚNICAMENTE el texto de la sugerencia. SIN comillas, SIN prefijos, SIN saltos de línea.
            4.  **CONTEXTO ES REY:** Basa tu sugerencia en el último mensaje del usuario y en lo que el reclutador está escribiendo.
            5.  **SUGERENCIA PROACTIVA:** Si el reclutador no ha escrito NADA ('current_text' está vacío), sugiere un saludo de apertura corto y profesional.

            ### EJEMPLOS DE COMPORTAMIENTO PERFECTO ###
            -   Historial: "Usuario: Hola, busco trabajo"
                Reclutador escribe: "¡Hola! Claro, con gusto"
                TU RESPUESTA: te ayudo.
            -   Historial: "Usuario: ¿Tienen vacantes en Tegucigalpa?"
                Reclutador escribe: "Sí, en este momento"
                TU RESPUESTA: tenemos varias opciones.
            -   Historial: "Usuario: Gracias"
                Reclutador escribe: ""
                TU RESPUESTA: ¿En qué más puedo ayudarte?

            ### EJEMPLOS DE COMPORTAMIENTO INCORRECTO (QUÉ NO HACER) ###
            -   Reclutador escribe: "Hola, de qué ciudad"
                TU RESPUESTA INCORRECTA: "¿Estás buscando empleo activamente?" (Esto es una pregunta nueva, no un autocompletado)
                TU RESPUESTA CORRECTA: nos contactas?

            ---
            ### TAREA ACTUAL ###
            HISTORIAL:
            ${formattedHistory}

            RECLUTADOR ESCRIBE: "${current_text}"

            AUTOCOMPLETADO SUGERIDO:`;

        const result = await geminiModel.generateContent(systemPrompt);
        const response = await result.response;
        const suggestion = response.text().trim();

        console.log(`[Copilot-Gemini] Texto: "${current_text}" -> Sugerencia: "${suggestion}"`);
        res.json({ suggestion });

    } catch (error) {
        console.error("❌ Error en el endpoint de sugerencia (Gemini):", error.message);
        res.status(500).json({ suggestion: '' });
    }
});



app.post('/api/crm/send-message', async (req, res) => {
    const { chatId, message } = req.body;

    if (!chatId || !message) {
        return res.status(400).json({ error: "Faltan chatId o message en la petición." });
    }

    // Verificamos si hay alguna sesión activa
    const activeSessions = sessionManager.getAllSessions();
    if (activeSessions.length === 0) {
        return res.status(503).json({ error: "No hay sesiones de WhatsApp activas." });
    }

    try {
        // 1. Enviar el mensaje a través de whatsapp-web.js
        console.log(`[Manual Send] Enviando mensaje a ${chatId}...`);
        await client.sendMessage(chatId, message);

        // 2. ✨ LÓGICA CLAVE: Desactivar el bot para esta conversación ✨
        // Actualizamos la base de datos para poner bot_active en 0 (desactivado).
        await new Promise((resolve, reject) => {
            db.run(
                "UPDATE conversations SET bot_active = 0 WHERE chat_id = ?",
                [chatId],
                (err) => {
                    if (err) {
                        console.error(`[Bot Pause] Error al desactivar el bot para ${chatId}:`, err.message);
                        // No rechazamos la promesa para que el mensaje se considere enviado,
                        // pero registramos el error.
                    } else {
                        console.log(`[Bot Pause] ✅ Bot desactivado automáticamente para ${chatId} por intervención humana.`);
                    }
                    resolve();
                }
            );
        });

        // 3. Devolver una respuesta exitosa al frontend
        res.json({ success: true, message: "Mensaje enviado y bot pausado para esta conversación." });

    } catch (error) {
        console.error(`[Manual Send] ❌ Error fatal al enviar mensaje a ${chatId}:`, error.message);
        res.status(500).json({ success: false, error: "No se pudo enviar el mensaje." });
    }
});



// Endpoint para Anclar / Desanclar un chat
app.post('/api/crm/chats/:chatId/pin', (req, res) => {
    const { chatId } = req.params;
    const { is_pinned } = req.body; // Esperamos un booleano: true para anclar, false para desanclar

    if (typeof is_pinned !== 'boolean') {
        return res.status(400).json({ error: "El estado 'is_pinned' debe ser un booleano." });
    }

    db.run(
        "UPDATE conversations SET is_pinned = ? WHERE chat_id = ?",
        [is_pinned ? 1 : 0, chatId],
        function (err) {
            if (err) {
                console.error(`Error al actualizar el estado de anclado para ${chatId}:`, err);
                return res.status(500).json({ error: "Error de base de datos." });
            }
            res.json({ success: true, message: `Chat ${is_pinned ? 'anclado' : 'desanclado'}.` });
        }
    );
});

// Endpoint para marcar un chat como leído (resetear el contador)
app.post('/api/crm/chats/:chatId/mark_read', (req, res) => {
    const { chatId } = req.params;

    db.run(
        "UPDATE conversations SET unread_count = 0 WHERE chat_id = ?",
        [chatId],
        function (err) {
            if (err) {
                console.error(`Error al marcar como leído para ${chatId}:`, err);
                return res.status(500).json({ error: "Error de base de datos." });
            }
            res.json({ success: true, message: "Chat marcado como leído." });
        }
    );
});

/**
 * Endpoint para DESACTIVAR las respuestas automáticas para un chat específico.
 * Esto sucede cuando un reclutador interviene manualmente.
 */
app.post('/api/crm/chats/:chatId/disable_bot', (req, res) => {
    const { chatId } = req.params;
    if (!chatId) {
        return res.status(400).json({ error: "Falta el ID del chat." });
    }

    console.log(`[Bot Control] Solicitud para DESACTIVAR el bot para el chat: ${chatId}`);

    const sql = "UPDATE conversations SET bot_active = 0 WHERE chat_id = ?";
    db.run(sql, [chatId], function (err) {
        if (err) {
            console.error(`Error al desactivar el bot para ${chatId}:`, err.message);
            return res.status(500).json({ error: "Error de base de datos." });
        }
        if (this.changes === 0) {
            // Esto puede pasar si el chat no existe, lo cual es poco probable pero posible.
            // Lo tratamos como un éxito para que la UI no se quede bloqueada.
            console.warn(`[Bot Control] No se encontró el chat ${chatId} para desactivar el bot, pero se responde con éxito.`);
        }
        res.json({ success: true, message: "Respuestas automáticas pausadas para este chat." });
    });
});


/**
 * Endpoint para REACTIVAR las respuestas automáticas para un chat específico.
 */
app.post('/api/crm/chats/:chatId/enable_bot', (req, res) => {
    const { chatId } = req.params;
    if (!chatId) {
        return res.status(400).json({ error: "Falta el ID del chat." });
    }

    console.log(`[Bot Control] Solicitud para REACTIVAR el bot para el chat: ${chatId}`);

    const sql = "UPDATE conversations SET bot_active = 1 WHERE chat_id = ?";
    db.run(sql, [chatId], function (err) {
        if (err) {
            console.error(`Error al reactivar el bot para ${chatId}:`, err.message);
            return res.status(500).json({ error: "Error de base de datos." });
        }
        if (this.changes === 0) {
            console.warn(`[Bot Control] No se encontró el chat ${chatId} para reactivar el bot, pero se responde con éxito.`);
        }
        res.json({ success: true, message: "Respuestas automáticas reactivadas para este chat." });
    });
});

// =================================================================
// --- ENDPOINTS DE WHATSAPP PARA CRM MULTI-TENANT ---
// =================================================================

/**
 * Middleware para validar tenant ID desde el CRM
 */
function validateTenantFromCRM(req, res, next) {
    // Obtener tenant ID desde headers o body
    const tenantId = req.headers['x-tenant-id'] || req.body?.tenantId;

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
 */
app.post('/api/whatsapp/session/init', validateTenantFromCRM, async (req, res) => {
    try {
        const { tenantId } = req;
        const userId = req.body?.userId || tenantId;

        console.log(`[WhatsApp API] Inicializando sesión para tenant: ${tenantId}`);

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
 */
app.get('/api/whatsapp/session/status', validateTenantFromCRM, (req, res) => {
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
 */
app.delete('/api/whatsapp/session/close', validateTenantFromCRM, async (req, res) => {
    try {
        const { tenantId } = req;

        console.log(`[WhatsApp API] Cerrando sesión para tenant: ${tenantId}`);

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
 */
app.get('/api/whatsapp/chats', validateTenantFromCRM, (req, res) => {
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
 */
app.get('/api/whatsapp/chats/:chatId/messages', validateTenantFromCRM, (req, res) => {
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
 */
app.post('/api/whatsapp/chats/:chatId/messages', validateTenantFromCRM, async (req, res) => {
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

        console.log(`[WhatsApp API] Enviando mensaje de ${tenantId} a ${chatId}`);

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
 */
app.get('/api/whatsapp/sessions', (req, res) => {
    try {
        // Verificar que sea administrador (simplificado para demo)
        const isAdmin = req.headers['x-admin'] === 'true';

        if (!isAdmin) {
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

// =================================================================
// --- NUEVO: ENDPOINT PARA EXTRAER NÚMEROS DE TELÉFONO ---
// =================================================================

/**
 * Endpoint para extraer todos los números de teléfono y nombres de contacto de WhatsApp
 */
app.get('/api/crm/extract_contacts', async (req, res) => {
    const activeSessions = sessionManager.getAllSessions();
    if (activeSessions.length === 0) {
        return res.status(503).json({
            error: "No hay sesiones de WhatsApp activas.",
            message: "Espera a que se inicialice una sesión de WhatsApp e inténtalo de nuevo."
        });
    }

    try {
        console.log('🔍 Iniciando extracción de contactos de WhatsApp...');

        // 1. Obtener todos los chats
        const chats = await client.getChats();

        // 2. Filtrar solo chats individuales (no grupos)
        const individualChats = chats.filter(chat => !chat.isGroup && chat.id.user);

        // 3. Obtener información adicional de cada contacto
        const contacts = [];
        let processedCount = 0;

        for (const chat of individualChats) {
            try {
                processedCount++;

                // Extraer información básica
                const phoneNumber = chat.id.user;
                let contactName = chat.name || 'Sin nombre';

                // Intentar obtener más información del contacto si está disponible
                try {
                    const contact = await client.getContactById(chat.id._serialized);
                    if (contact.name && contact.name.trim() !== '') {
                        contactName = contact.name;
                    } else if (contact.pushname && contact.pushname.trim() !== '') {
                        contactName = contact.pushname;
                    }
                } catch (contactError) {
                    // Si no se puede obtener info del contacto, seguimos con el nombre del chat
                }

                // Formatear el número de teléfono
                const formattedPhone = phoneNumber.includes('@') ? phoneNumber : `${phoneNumber}@c.us`;

                contacts.push({
                    phone_number: phoneNumber,
                    formatted_phone: formattedPhone,
                    contact_name: contactName,
                    chat_id: chat.id._serialized,
                    last_message_time: chat.timestamp ? new Date(chat.timestamp * 1000).toISOString() : null,
                    unread_count: chat.unreadCount || 0,
                    is_archived: chat.archived || false
                });

                // Log de progreso cada 100 contactos
                if (processedCount % 100 === 0) {
                    console.log(`📱 Procesados ${processedCount}/${individualChats.length} contactos...`);
                }

            } catch (error) {
                console.warn(`⚠️ Error procesando contacto ${chat.id._serialized}:`, error.message);
                // Continuar con el siguiente contacto
            }
        }

        // 4. Ordenar por nombre
        contacts.sort((a, b) => a.contact_name.localeCompare(b.contact_name));

        console.log(`✅ Extracción completada: ${contacts.length} contactos extraídos de ${individualChats.length} chats individuales.`);

        res.json({
            success: true,
            message: `Extracción completada exitosamente`,
            total_contacts: contacts.length,
            total_chats_processed: individualChats.length,
            extraction_timestamp: new Date().toISOString(),
            contacts: contacts
        });

    } catch (error) {
        console.error("❌ Error fatal durante la extracción de contactos:", error.message);
        res.status(500).json({
            success: false,
            error: "Error interno durante la extracción de contactos",
            message: error.message
        });
    }
});

/**
 * Endpoint para exportar contactos en formato CSV
 */
app.get('/api/crm/export_contacts_csv', async (req, res) => {
    const activeSessions = sessionManager.getAllSessions();
    if (activeSessions.length === 0) {
        return res.status(503).json({
            error: "No hay sesiones de WhatsApp activas."
        });
    }

    try {
        console.log('📊 Iniciando exportación CSV de contactos...');

        const chats = await client.getChats();
        const individualChats = chats.filter(chat => !chat.isGroup && chat.id.user);

        // Crear contenido CSV
        let csvContent = 'Nombre,Numero_Telefono,Numero_Formateado,Ultimo_Mensaje,Mensajes_No_Leidos,Archivado\n';

        for (const chat of individualChats) {
            try {
                const phoneNumber = chat.id.user;
                let contactName = chat.name || 'Sin nombre';

                try {
                    const contact = await client.getContactById(chat.id._serialized);
                    if (contact.name && contact.name.trim() !== '') {
                        contactName = contact.name;
                    } else if (contact.pushname && contact.pushname.trim() !== '') {
                        contactName = contact.pushname;
                    }
                } catch (contactError) {
                    // Continuar con el nombre del chat
                }

                const formattedPhone = phoneNumber.includes('@') ? phoneNumber : `${phoneNumber}@c.us`;
                const lastMessageTime = chat.timestamp ? new Date(chat.timestamp * 1000).toISOString() : '';
                const unreadCount = chat.unreadCount || 0;
                const isArchived = chat.archived ? 'Si' : 'No';

                // Escapar comillas en el nombre
                const escapedName = contactName.replace(/"/g, '""');

                csvContent += `"${escapedName}","${phoneNumber}","${formattedPhone}","${lastMessageTime}","${unreadCount}","${isArchived}"\n`;

            } catch (error) {
                console.warn(`⚠️ Error procesando contacto para CSV ${chat.id._serialized}:`, error.message);
            }
        }

        // Configurar headers para descarga de archivo
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        const filename = `contactos_whatsapp_${timestamp}.csv`;

        res.setHeader('Content-Type', 'text/csv; charset=utf-8');
        res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
        res.setHeader('Content-Length', Buffer.byteLength(csvContent, 'utf8'));

        console.log(`✅ Exportación CSV completada: ${individualChats.length} contactos exportados.`);

        res.send('\ufeff' + csvContent); // BOM para UTF-8

    } catch (error) {
        console.error("❌ Error fatal durante la exportación CSV:", error.message);
        res.status(500).json({
            success: false,
            error: "Error interno durante la exportación CSV"
        });
    }
});

// =================================================================
// --- 5. LÓGICA DEL WEBSOCKET (PARA ASISTENTE Y CAMPAÑAS) ---
// =================================================================

/**
 * Configura el servidor WebSocket para comunicación en tiempo real con el frontend
 * @param {Object} server - Servidor HTTP de Express
 * @returns {WebSocket.Server} Instancia del servidor WebSocket
 */
function setupWebSocketServer(server) {
    const wss = new WebSocket.Server({
        server,
        clientTracking: true,
        perMessageDeflate: {
            zlibDeflateOptions: {
                chunkSize: 1024,
                memLevel: 7,
                level: 3,
            },
            zlibInflateOptions: {
                chunkSize: 10 * 1024,
            },
            clientNoContextTakeover: true,
            serverNoContextTakeover: true,
            serverMaxWindowBits: 10,
            concurrencyLimit: 10,
            threshold: 1024,
        },
    });

    // Limpiar conexiones existentes al iniciar
    webSocketClients.clear();

    wss.on('connection', (ws, req) => {
        const clientId = Date.now().toString();
        console.log(`🔌 Nueva conexión WebSocket [${clientId}]`);

        // Almacenar la conexión
        webSocketClients.set(clientId, ws);
        crmSocket = ws; // Mantener compatibilidad con código existente

        // Heartbeat
        ws.isAlive = true;
        ws.on('pong', () => {
            ws.isAlive = true;
        });

        // Enviar estado inicial
        sendInitialState(ws);

        // Manejar mensajes entrantes
        ws.on('message', async (data) => {
            try {
                const message = JSON.parse(data);
                await handleWebSocketMessage(clientId, message);
            } catch (error) {
                console.error('❌ Error al procesar mensaje WebSocket:', error);
                sendError(clientId, 'invalid_message', 'Formato de mensaje inválido');
            }
        });

        // Manejar cierre de conexión
        ws.on('close', () => {
            console.log(`🔌 Conexión WebSocket cerrada [${clientId}]`);
            webSocketClients.delete(clientId);
            if (crmSocket === ws) {
                crmSocket = null;
            }
        });

        // Manejar errores
        ws.on('error', (error) => {
            console.error(`❌ Error en la conexión WebSocket [${clientId}]:`, error);
            webSocketClients.delete(clientId);
            if (crmSocket === ws) {
                crmSocket = null;
            }
        });
    });

    // Heartbeat para mantener la conexión activa
    const heartbeatInterval = setInterval(() => {
        webSocketClients.forEach((ws, clientId) => {
            if (ws.isAlive === false) {
                console.log(`💔 Conexión inactiva, cerrando [${clientId}]`);
                return ws.terminate();
            }

            ws.isAlive = false;
            ws.ping();
        });
    }, 30000);

    // Limpiar el intervalo cuando el servidor se cierra
    wss.on('close', () => {
        clearInterval(heartbeatInterval);
    });

    /**
     * Envía el estado inicial de las sesiones al cliente WebSocket
     * @param {WebSocket} ws - Conexión WebSocket del cliente
     */
    function sendInitialState(ws) {
        try {
            const sessionsData = Array.from(activeSessions.entries()).map(([id, session]) => ({
                sessionId: id,
                status: session.status,
                tenantId: session.tenantId,
                lastActivity: session.lastActivity.toISOString(),
                proxy: session.proxy,
                qrCode: session.qrCode,
                isReady: session.status === 'ready',
            }));

            const response = {
                type: 'initial_state',
                timestamp: new Date().toISOString(),
                sessions: sessionsData,
                totalSessions: sessionsData.length
            };

            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify(response));
            }
        } catch (error) {
            console.error('Error al enviar estado inicial:', error);
        }
    }
    /**
     * Maneja los mensajes entrantes del WebSocket
     * @param {string} clientId - ID del cliente WebSocket
     * @param {Object} message - Mensaje recibido
     * @returns {Promise<void>}
     */
    async function handleWebSocketMessage(clientId, message) {
        if (!message || typeof message !== 'object') {
            console.error('Mensaje WebSocket inválido:', message);
            return;
        }

        const { type, payload } = message;
        const ws = webSocketClients.get(clientId);

        if (!ws) {
            console.error(`Cliente no encontrado: ${clientId}`);
            return;
        }

        try {
            switch (type) {
                case 'init_session':
                    const { sessionId, tenantId } = payload;
                    const result = await startSession(sessionId, tenantId);
                    ws.send(JSON.stringify({
                        type: 'session_initialized',
                        ...result
                    }));
                    break;

                case 'send_message':
                    const { sessionId: msgSessionId, chatId, message: msg } = payload;
                    const sendResult = await sendMessageToSession(msgSessionId, chatId, msg);
                    ws.send(JSON.stringify({
                        type: 'message_sent',
                        ...sendResult
                    }));
                    break;

                case 'get_session_status':
                    const { sessionId: statusSessionId } = payload;
                    const session = activeSessions.get(statusSessionId);
                    ws.send(JSON.stringify({
                        type: 'session_status',
                        sessionId: statusSessionId,
                        status: session ? session.status : 'not_found',
                        lastActivity: session?.lastActivity?.toISOString(),
                        proxy: session?.proxy
                    }));
                    break;

                case 'close_session':
                    const { sessionId: closeSessionId } = payload;
                    await cleanupSession(closeSessionId);
                    ws.send(JSON.stringify({
                        type: 'session_closed',
                        sessionId: closeSessionId,
                        success: true
                    }));
                    break;

                case 'queue_campaign_task':
                    if (payload.task) {
                        const { telefono, mensaje, nombre } = payload.task;
                        const chatId = `${telefono.replace(/\D/g, '')}@c.us`;
                        await client.sendMessage(chatId, mensaje);
                        ws.send(JSON.stringify({
                            type: 'log',
                            success: true,
                            message: `Éxito: Campaña enviada a ${nombre}`
                        }));
                    }
                    break;

                case 'queue_notification_task':
                    if (payload.task) {
                        const { task_type, related_id, chat_id, message_body } = payload.task;
                        const HONDURAS_TIMEZONE = 'America/Tegucigalpa';
                        const now_hn = moment().tz(HONDURAS_TIMEZONE);
                        let scheduled_time;
                        if (now_hn.hour() >= 8 && now_hn.hour() < 19) {
                            scheduled_time = moment().add(10, 'seconds');
                        } else {
                            scheduled_time = now_hn.add(1, 'day').hour(8).minute(0).second(0);
                        }
                        const scheduled_for_timestamp = scheduled_time.unix();
                        const sql = `INSERT INTO Whatsapp_Queue_Local (task_type, related_id, chat_id, message_body, scheduled_for) VALUES (?, ?, ?, ?, ?)`;
                        db.run(sql, [task_type, related_id, chat_id, message_body, scheduled_for_timestamp]);
                    }
                    break;
            }
        } catch (e) {
            console.error("Error procesando mensaje de WebSocket:", e);
            ws.send(JSON.stringify({ type: 'log', success: false, message: `Error en WebSocket: ${e.message}` }));
        }
    }

    return wss;
}

// =================================================================
// --- 6. INICIALIZACIÓN DEL CLIENTE DE WHATSAPP ---
// =================================================================
async function initializeWhatsappClient() {
    console.log('🔍 Inicializando cliente de WhatsApp...');

    // Generar un ID de sesión único basado en la hora actual
    const sessionId = `session_${Date.now()}`;

    // Obtener proxy para esta sesión
    const proxyConfig = getUniqueProxyForSession(sessionId);

    // Configurar opciones de Puppeteer
    const puppeteerConfig = {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--disable-gpu'
        ]
    };

    // Configuración de path de Chromium para entornos Linux/Server (Oracle Cloud)
    if (process.env.PUPPETEER_EXECUTABLE_PATH) {
        puppeteerConfig.executablePath = process.env.PUPPETEER_EXECUTABLE_PATH;
    } else if (process.platform === 'linux') {
        const commonPaths = ['/usr/bin/chromium-browser', '/usr/bin/chromium', '/snap/bin/chromium'];
        for (const p of commonPaths) {
            if (fs.existsSync(p)) {
                console.log(`🐧 Usando Chromium en: ${p}`);
                puppeteerConfig.executablePath = p;
                break;
            }
        }
    }

    if (!puppeteerConfig.executablePath) {
        console.log('ℹ️  Usando Chromium empaquetado con Puppeteer');
    }

    // Configurar Proxy si existe
    if (proxyConfig) {
        const { server, username, password } = proxyConfig;
        const auth = username && password ? `${username}:${password}@` : '';
        const proxyUrl = `http://${auth}${server}`;

        console.log(`🌐 Usando proxy: ${server}`);
        puppeteerConfig.args.push(`--proxy-server=${proxyUrl}`);

        if (username && password) {
            puppeteerConfig.args.push(`--proxy-auth=${username}:${password}`);
        }
    } else {
        console.log('⚠️  No se configuró ningún proxy. Usando conexión directa.');
    }

    // Configuración del cliente con autenticación local
    client = new Client({
        authStrategy: new LocalAuth({
            clientId: 'crm-whatsapp-client',
            dataPath: './sessions',
        }),
        puppeteer: puppeteerConfig
    });


    // 2. Adjuntamos TODOS los listeners de eventos al objeto 'client'
    client.on('qr', async (qr) => {
        console.log('QR Recibido.');

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

            // Mostrar QR en terminal también
            console.log('🔑 Código QR generado');
            qrcodeTerminal.generate(qr, { small: true });

            // Enviar imagen base64 al frontend
            if (crmSocket) {
                crmSocket.send(JSON.stringify({
                    type: 'qr',
                    data: qrImageBase64
                }));
            }
        } catch (error) {
            console.error('Error generando QR como imagen:', error);
            // Fallback: enviar QR como texto
            if (crmSocket) {
                crmSocket.send(JSON.stringify({ type: 'qr', data: qr }));
            }
        }
    });

    client.on('ready', async () => {
        console.log('✅ Cliente de WhatsApp está listo y conectado.');
        if (crmSocket) crmSocket.send(JSON.stringify({ type: 'status', message: 'Conectado' }));

        console.log('⏳ Sincronizando lista de chats inicial...');
        try {
            const chats = await client.getChats();
            const userChats = chats.filter(chat => !chat.isGroup && chat.id.user);
            db.serialize(() => {
                // AÑADE ESTE BLOQUE TEMPORALMENTE EN bridge.js DENTRO DE db.serialize
                console.log("⏳ MIGRACIÓN DE ESTADO: Corrigiendo estados 'identified_affiliate' antiguos...");
                db.run("UPDATE conversations SET status = 'AFFILIATE_LOGGED_IN' WHERE status = 'identified_affiliate'", function (err) {
                    if (err) {
                        console.error("❌ Error en la migración de estado:", err.message);
                    } else if (this.changes > 0) {
                        console.log(`✅ Migración de estado completada. ${this.changes} registros actualizados.`);
                    } else {
                        console.log("✅ No se encontraron estados antiguos para migrar.");
                    }
                });
                const stmt = db.prepare(`INSERT INTO conversations (chat_id, contact_name, last_message_timestamp) VALUES (?, ?, ?) ON CONFLICT(chat_id) DO UPDATE SET contact_name = excluded.contact_name, last_message_timestamp = MAX(last_message_timestamp, excluded.last_message_timestamp)`);
                for (const chat of userChats) {
                    stmt.run(chat.id._serialized, chat.name || chat.id.user, chat.timestamp || 0);
                }
                stmt.finalize((err) => {
                    if (err) console.error("❌ Error al finalizar sincronización de chats:", err.message);
                    else console.log(`✅ Sincronización completada. ${userChats.length} chats procesados.`);
                    if (crmSocket) crmSocket.send(JSON.stringify({ type: 'chats_synced' }));
                });
            });

            console.log("[Auto-Sync] Iniciando resincronización de notificaciones pendientes con el backend...");
            const url = `${process.env.CRM_API_URL}/api/applications/resync_pending_notifications`;
            fetch(url, {
                method: 'POST',
                headers: { 'X-API-Key': process.env.CRM_INTERNAL_API_KEY }
            }).then(res => res.json())
                .then(data => console.log(`[Auto-Sync] Respuesta de resincronización: ${data.tasks_resent || 0} tareas reenviadas.`))
                .catch(err => console.error("[Auto-Sync] ❌ Error durante la resincronización automática:", err.message));

        } catch (error) {
            console.error("❌ Error durante la sincronización inicial de chats:", error);
        }
    });

    client.on('disconnected', (reason) => {
        console.log('❌ Cliente de WhatsApp desconectado:', reason);
        if (crmSocket) crmSocket.send(JSON.stringify({ type: 'status', message: 'Desconectado', error: true }));
    });

    client.on('message', (msg) => {
        if (!msg.hasMedia) {
            archiveAndAnalyze(msg, false);
        }
    });

    client.on('message_create', (msg) => {
        if (msg.fromMe) {
            archiveAndAnalyze(msg, true);
        }
    });

    // 3. Y finalmente, inicializamos el cliente
    client.initialize().catch(err => {
        console.error("❌ FALLO CRÍTICO AL INICIALIZAR WHATSAPP:", err);
    });
}


// REEMPLAZA ESTA FUNCIÓN COMPLETA

const archiveAndAnalyze = async (msg, fromMe) => {
    const chatId = fromMe ? msg.to : msg.from;
    const contactName = msg._data.notifyName || (await msg.getContact())?.name || chatId.split('@')[0];
    const messageBody = msg.body;

    try {
        // La lógica de guardar en la base de datos se mantiene igual (ya es robusta)
        await new Promise(resolve => db.run('BEGIN TRANSACTION', resolve));

        if (messageBody) {
            await new Promise((resolve, reject) => {
                db.run(`INSERT INTO messages (chat_id, sender, body, timestamp, from_me) VALUES (?, ?, ?, ?, ?)`,
                    [chatId, fromMe ? 'me' : 'user', messageBody, msg.timestamp, fromMe],
                    err => err ? reject(err) : resolve());
            });
        }

        const upsertConversationSql = `
            INSERT INTO conversations (chat_id, contact_name, last_message_timestamp, status, unread_count)
            VALUES (?, ?, ?, 'new_visitor', 1)
            ON CONFLICT(chat_id) DO UPDATE SET
                contact_name = excluded.contact_name,
                last_message_timestamp = excluded.last_message_timestamp,
                unread_count = CASE WHEN ? THEN unread_count ELSE unread_count + 1 END;
        `;
        await new Promise((resolve, reject) => {
            db.run(upsertConversationSql, [chatId, contactName, msg.timestamp, fromMe], function (err) {
                if (err) return reject(err);
                if (this.changes > 0 && !fromMe) {
                    console.log(`[New Conversation] Detectado primer mensaje de ${chatId}.`);
                    db.run("UPDATE conversations SET status = 'AWAITING_AFFILIATION_CONFIRM' WHERE chat_id = ?", [chatId]);
                }
                resolve();
            });
        });

        await new Promise(resolve => db.run('COMMIT', resolve));

        // Notificar a la UI del CRM en tiempo real (sin cambios)
        if (crmSocket && crmSocket.readyState === 1) { // <-- ¡ERROR CORREGIDO AQUÍ!
            const conversationData = await new Promise((resolve, reject) => {
                db.get("SELECT * FROM conversations WHERE chat_id = ?", [chatId], (err, row) => err ? reject(err) : resolve(row));
            });
            const newMessageNotification = { type: 'new_message', data: { id: chatId, name: contactName, custom_name: conversationData?.custom_name, status: conversationData?.status, lastMessage: messageBody || '[Mensaje Multimedia]', timestamp: msg.timestamp, lastMessageFromMe: fromMe, unread_count: conversationData?.unread_count, is_pinned: conversationData?.is_pinned, messageObject: { chat_id: chatId, body: messageBody, timestamp: msg.timestamp, from_me: fromMe } } };
            crmSocket.send(JSON.stringify(newMessageNotification));
        }

        // --- ¡NUEVA LÓGICA DE COLA DE ANÁLISIS! ---
        // Si el mensaje no es nuestro, lo añadimos a la cola para ser analizado
        if (!fromMe) {
            console.log(`[Queue] Chat ${chatId} añadido a la cola de análisis.`);
            analysisQueue.add(chatId);
        }

    } catch (error) {
        await new Promise(resolve => db.run('ROLLBACK', () => resolve()));
        // Aquí NO usamos WebSocket.OPEN porque estamos en Node.js
        console.error(`❌ Error fatal durante archiveAndAnalyze para ${chatId}:`, error);
    }
};

// AÑADE ESTE BLOQUE COMPLETO DE CÓDIGO NUEVO

/**
 * Procesa la cola de chats que necesitan análisis por IA.
 * Se ejecuta periódicamente para agrupar peticiones y respetar los límites de la API.
 */
async function processAnalysisQueue() {
    if (isAnalysisRunning || analysisQueue.size === 0) {
        return; // Si ya se está procesando o la cola está vacía, no hace nada
    }

    isAnalysisRunning = true;
    console.log(`[Analysis Worker] Iniciando procesamiento de ${analysisQueue.size} chats en cola.`);

    // Hacemos una copia de la cola y la limpiamos para que nuevos mensajes se acumulen
    const chatsToProcess = [...analysisQueue];
    analysisQueue.clear();

    for (const chatId of chatsToProcess) {
        try {
            // Obtenemos el historial más reciente para el análisis
            const history = await new Promise((resolve, reject) => {
                db.all('SELECT * FROM messages WHERE chat_id = ? ORDER BY timestamp DESC LIMIT 5', [chatId], (err, rows) => {
                    if (err) return reject(err);
                    resolve(rows.reverse());
                });
            });

            if (!history || history.length === 0) continue;

            // Llamamos a la función de análisis
            const analysis = await analyzeConversationWithGemini(history);
            if (!analysis) continue;

            // Si el análisis indica que requiere atención, creamos la notificación
            const requiresAttention = analysis.sentiment === 'negativo' || analysis.urgency === 'alta';
            if (requiresAttention) {
                const conversation = await new Promise((resolve, reject) => {
                    db.get('SELECT contact_name FROM conversations WHERE chat_id = ?', [chatId], (err, row) => err ? reject(err) : resolve(row));
                });
                if (!conversation) continue;

                const notificationType = 'human_intervention_required';
                const insertQuery = `INSERT INTO notifications (chat_id, contact_name, type, summary, timestamp) VALUES (?, ?, ?, ?, ?)`;
                const insertParams = [chatId, conversation.contact_name, notificationType, analysis.summary, Math.floor(Date.now() / 1000)];

                db.run(insertQuery, insertParams, function (err) {
                    if (err) return console.error(`[Analysis Worker] Error guardando notificación para ${chatId}:`, err);

                    // Notificar a la UI del CRM en tiempo real
                    const newNotificationData = { id: this.lastID, chat_id: chatId, contact_name: conversation.contact_name, type: notificationType, summary: analysis.summary };
                    if (crmSocket && crmSocket.readyState === 1) { // <-- ¡ERROR CORREGIDO AQUÍ TAMBIÉN!
                        crmSocket.send(JSON.stringify({ type: 'new_notification', data: newNotificationData }));
                    }
                });
            }
        } catch (error) {
            console.error(`[Analysis Worker] ❌ Error procesando el chat ${chatId}:`, error);
        }
    }

    console.log('[Analysis Worker] Procesamiento de la cola finalizado.');
    isAnalysisRunning = false;
}

// Ejecuta el procesador de la cola de análisis cada 15 segundos.
// Esto agrupa las peticiones, resultando en un máximo de 4 llamadas por minuto.
setInterval(processAnalysisQueue, 15 * 1000);


/**
 * Función que arranca todos los servidores y clientes.
 * Se llama ÚNICAMENTE después de que la base de datos está confirmada como lista.
 */
function startApp() {
    const PORT = process.env.PORT || 3000;

    // 1. Crear el servidor HTTP a partir de la app de Express
    const server = require('http').createServer(app);

    // 2. Adjuntar el servidor WebSocket a nuestro servidor HTTP
    setupWebSocketServer(server);

    // 3. Iniciar el servidor para que escuche peticiones
    server.listen(PORT, () => {
        console.log(`✅ Servidor Express y WebSocket escuchando en http://localhost:${PORT}`);

        // 4. Realizar la prueba de conectividad
        fetch('https://www.google.com', { method: 'HEAD' })
            .then(res => console.log(res.ok ? "✅ Prueba de conectividad a internet exitosa." : "❌ Prueba de conectividad fallida."))
            .catch(err => console.error("❌ FALLO CRÍTICO de fetch:", err.message));

        // 5. Finalmente, inicializar el cliente de WhatsApp
        initializeWhatsappClient();
    });
}
