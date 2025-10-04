/**
 * Script de prueba para verificar el backend de WhatsApp
 */

console.log('🧪 Iniciando pruebas del backend WhatsApp...');

// Verificar que las dependencias estén instaladas
try {
    const express = require('express');
    const { Client } = require('whatsapp-web.js');
    const WebSocket = require('ws');
    const sqlite3 = require('sqlite3');
    
    console.log('✅ Todas las dependencias principales están disponibles');
} catch (error) {
    console.error('❌ Error importando dependencias:', error.message);
    process.exit(1);
}

// Verificar que los archivos del sistema existan
const fs = require('fs');
const path = require('path');

const requiredFiles = [
    'whatsapp-session-manager.js',
    'whatsapp-api-official.js',
    'bridge.js'
];

console.log('📁 Verificando archivos del sistema...');
for (const file of requiredFiles) {
    if (fs.existsSync(path.join(__dirname, file))) {
        console.log(`✅ ${file} encontrado`);
    } else {
        console.log(`❌ ${file} no encontrado`);
    }
}

// Verificar configuración de entorno
console.log('🔧 Verificando configuración de entorno...');
const envVars = [
    'PORT',
    'OPENAI_API_KEY',
    'GEMINI_API_KEY',
    'CRM_API_URL'
];

for (const envVar of envVars) {
    if (process.env[envVar]) {
        console.log(`✅ ${envVar} configurado`);
    } else {
        console.log(`⚠️  ${envVar} no configurado (opcional)`);
    }
}

// Probar importación del session manager
try {
    const sessionManager = require('./whatsapp-session-manager');
    console.log('✅ WhatsApp Session Manager importado correctamente');
    
    // Probar método básico
    const sessions = sessionManager.getAllSessions();
    console.log(`✅ Session Manager funcional - Sesiones activas: ${sessions.length}`);
} catch (error) {
    console.error('❌ Error importando Session Manager:', error.message);
}

// Probar importación de la API oficial
try {
    const whatsappAPI = require('./whatsapp-api-official');
    console.log('✅ WhatsApp Official API importado correctamente');
    
    // Probar método básico
    const sessions = whatsappAPI.getAllSessions();
    console.log(`✅ WhatsApp API funcional - Sesiones activas: ${sessions.length}`);
} catch (error) {
    console.error('❌ Error importando WhatsApp API:', error.message);
}

console.log('🎉 Pruebas completadas!');
console.log('📋 Para iniciar el servidor, ejecuta: npm start');
console.log('📋 Para desarrollo, ejecuta: npm run dev');
