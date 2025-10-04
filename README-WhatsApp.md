# 📱 WhatsApp Integration para Zenno CRM

## 🎯 Descripción

Sistema completo de integración de WhatsApp con el CRM Zenno, que incluye:
- **WhatsApp Web.js** - Conexión directa con cuentas personales/empresariales
- **WhatsApp Business API** - API oficial de Meta para funcionalidades empresariales
- **Multi-tenancy** - Sesiones aisladas por usuario/tenant
- **Tiempo real** - Mensajes instantáneos via WebSocket
- **Interfaz moderna** - Panel de conversaciones integrado en el CRM

## 🚀 Instalación

### 1. Instalar dependencias
```bash
npm install
```

### 2. Configurar variables de entorno
Copia `env.example` a `.env` y configura las variables necesarias:

```bash
cp env.example .env
```

Variables principales:
```env
PORT=3000
CRM_API_URL=http://localhost:5000
OPENAI_API_KEY=tu_clave_openai
GEMINI_API_KEY=tu_clave_gemini
```

### 3. Verificar instalación
```bash
node test-whatsapp-backend.js
```

## 🏃‍♂️ Uso

### Iniciar el servidor
```bash
# Producción
npm start

# Desarrollo (con auto-reload)
npm run dev
```

### Verificar funcionamiento
El servidor estará disponible en `http://localhost:3000`

## 📡 Endpoints API

### Sesiones WhatsApp
- `POST /api/whatsapp/session/init` - Inicializar sesión
- `GET /api/whatsapp/session/status` - Estado de sesión
- `DELETE /api/whatsapp/session/close` - Cerrar sesión

### Conversaciones
- `GET /api/whatsapp/chats` - Lista de chats
- `GET /api/whatsapp/chats/:id/messages` - Mensajes de chat
- `POST /api/whatsapp/chats/:id/messages` - Enviar mensaje

### Administración
- `GET /api/whatsapp/sessions` - Todas las sesiones (admin)

## 🔧 Configuración

### WhatsApp Web.js
- **Automático** - Solo necesitas escanear el QR
- **Sin costos** - Usa tu cuenta personal/empresarial
- **Fácil setup** - Configuración en minutos

### WhatsApp Business API
Requiere configuración adicional:
1. **Token de acceso** de Meta Business
2. **Phone Number ID** verificado
3. **Webhook URL** configurada
4. **Plantillas** aprobadas por Meta

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend        │    │   WhatsApp      │
│   (React)       │◄──►│   (Node.js)      │◄──►│   Web/API       │
│                 │    │                  │    │                 │
│ - Conversations │    │ - Session Manager│    │ - QR Scanner    │
│ - Real-time     │    │ - WebSocket      │    │ - Messages      │
│ - Mode Selector │    │ - API Endpoints  │    │ - Templates     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔐 Seguridad

- **Multi-tenancy** - Aislamiento completo entre usuarios
- **Validación de tenant** - Cada request verifica permisos
- **WebSocket seguro** - Conexiones autenticadas
- **Tokens JWT** - Autenticación robusta

## 📊 Monitoreo

### Logs del sistema
```bash
# Ver logs en tiempo real
npm run dev
```

### Métricas disponibles
- Sesiones activas por tenant
- Mensajes enviados/recibidos
- Estado de conexiones
- Errores y reconexiones

## 🐛 Troubleshooting

### Problemas comunes

**Error: "Module not found"**
```bash
npm install
```

**Error: "Port already in use"**
```bash
# Cambiar puerto en .env
PORT=3001
```

**WhatsApp no conecta**
1. Verificar conexión a internet
2. Revisar firewall/antivirus
3. Probar con VPN si es necesario

**QR no aparece**
1. Verificar logs del servidor
2. Revisar configuración de Puppeteer
3. Reiniciar el servidor

## 📈 Próximas mejoras

- [ ] Métricas y analytics avanzados
- [ ] Plantillas de mensajes automáticas
- [ ] Integración con IA para respuestas
- [ ] Backup automático de conversaciones
- [ ] API para integraciones externas

## 🤝 Soporte

Para soporte técnico:
1. Revisar logs del servidor
2. Verificar configuración de entorno
3. Consultar documentación de dependencias
4. Contactar al equipo de desarrollo

---

**Versión:** 1.0.0  
**Última actualización:** Diciembre 2024  
**Desarrollado por:** Zenno CRM Team
