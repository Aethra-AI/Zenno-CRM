# 📱 PLAN DETALLADO: ARQUITECTURA MULTI-TENANT WHATSAPP

## 🎯 **SITUACIÓN ACTUAL vs OBJETIVO**

### **Sistema Actual (WhatsApp Web.js)**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Bridge.js      │    │  WhatsApp Web   │
│  Conversations  │◄──►│  (Node.js)       │◄──►│     Session     │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Limitaciones Actuales:**
- ❌ **Dependencia de WhatsApp Web**: Requiere mantener sesión activa
- ❌ **Sin aislamiento por tenant**: Una sola instancia para todos
- ❌ **Limitado a mensajes**: No maneja conversaciones complejas
- ❌ **Inestable**: Sesiones se pierden frecuentemente
- ❌ **Sin escalabilidad**: No puede manejar múltiples usuarios simultáneos

### **Objetivo (API Oficial + WhatsApp Web Híbrido)**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   CRM Backend    │    │  WhatsApp API   │
│  Conversations  │◄──►│   (Multi-tenant) │◄──►│   (Oficial)     │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  WhatsApp Web    │
                    │  (Fallback)      │
                    └──────────────────┘
```

## 🏗️ **ARQUITECTURA PROPUESTA**

### **1. COMPONENTES PRINCIPALES**

#### **A. Sistema Central de Webhooks**
```python
# webhook_router.py
class WhatsAppWebhookRouter:
    def __init__(self):
        self.tenant_apis = {}  # Mapeo tenant_id -> config API
    
    def route_webhook(self, webhook_data):
        # 1. Identificar tenant por phone_number_id
        tenant_id = self.identify_tenant(webhook_data['phone_number_id'])
        
        # 2. Enrutar a la API correspondiente del tenant
        api_config = self.get_tenant_api_config(tenant_id)
        
        # 3. Procesar mensaje y guardar en BD
        self.process_message(tenant_id, webhook_data)
```

#### **B. Gestor Multi-Tenant de APIs**
```python
# whatsapp_api_manager.py
class WhatsAppAPIManager:
    def __init__(self):
        self.tenant_configs = {}  # Configuraciones por tenant
    
    def send_message(self, tenant_id, message_data):
        config = self.get_tenant_config(tenant_id)
        
        if config['api_type'] == 'business_api':
            return self.send_via_business_api(config, message_data)
        elif config['api_type'] == 'whatsapp_web':
            return self.send_via_web(config, message_data)
```

#### **C. Base de Datos de Configuración**
```sql
-- Tabla de configuración de WhatsApp por tenant
CREATE TABLE WhatsApp_Config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    api_type ENUM('business_api', 'whatsapp_web') NOT NULL,
    
    -- Configuración Business API
    business_api_token VARCHAR(500),
    phone_number_id VARCHAR(50),
    webhook_verify_token VARCHAR(100),
    business_account_id VARCHAR(50),
    
    -- Configuración WhatsApp Web
    web_session_id VARCHAR(100),
    web_qr_code TEXT,
    web_status ENUM('disconnected', 'qr_ready', 'connected') DEFAULT 'disconnected',
    
    -- Configuración común
    webhook_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id),
    UNIQUE KEY unique_tenant_api (tenant_id, api_type)
);

-- Tabla de conversaciones
CREATE TABLE WhatsApp_Conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    conversation_id VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    contact_name VARCHAR(100),
    last_message_at TIMESTAMP,
    status ENUM('active', 'archived', 'blocked') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id),
    UNIQUE KEY unique_conversation (tenant_id, conversation_id)
);

-- Tabla de mensajes
CREATE TABLE WhatsApp_Messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    conversation_id INT NOT NULL,
    message_id VARCHAR(100) NOT NULL,
    direction ENUM('inbound', 'outbound') NOT NULL,
    message_type ENUM('text', 'image', 'document', 'audio', 'video') NOT NULL,
    content TEXT,
    media_url VARCHAR(500),
    status ENUM('sent', 'delivered', 'read', 'failed') DEFAULT 'sent',
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tenant_id) REFERENCES Tenants(id),
    FOREIGN KEY (conversation_id) REFERENCES WhatsApp_Conversations(id),
    INDEX idx_conversation_timestamp (conversation_id, timestamp)
);
```

## 🔄 **FLUJO DE FUNCIONAMIENTO**

### **Escenario 1: Mensaje Entrante (Webhook)**
```
1. WhatsApp Business API → Webhook URL
2. Sistema identifica tenant por phone_number_id
3. Guarda mensaje en BD del tenant correspondiente
4. Notifica al frontend via WebSocket
5. Usuario ve mensaje en su interfaz
```

### **Escenario 2: Mensaje Saliente (CRM)**
```
1. Usuario envía mensaje desde CRM
2. Sistema identifica tenant del usuario
3. Busca configuración WhatsApp del tenant
4. Envía via API correspondiente (Business API o Web)
5. Guarda mensaje en BD
6. Actualiza estado en tiempo real
```

### **Escenario 3: Notificaciones Automáticas**
```
1. Evento en CRM (postulación, entrevista, etc.)
2. Sistema busca plantilla correspondiente
3. Identifica destinatario y tenant
4. Envía mensaje via configuración del tenant
5. Registra en historial
```

## 🎛️ **CONFIGURACIÓN POR TENANT**

### **Opciones de Configuración:**

#### **Opción A: WhatsApp Business API (Recomendado)**
```json
{
  "api_type": "business_api",
  "business_api_token": "EAAxxxx...",
  "phone_number_id": "123456789012345",
  "webhook_verify_token": "mi_token_secreto",
  "business_account_id": "123456789012345"
}
```

#### **Opción B: WhatsApp Web (Fallback)**
```json
{
  "api_type": "whatsapp_web",
  "web_session_id": "tenant_1_session",
  "web_status": "connected",
  "fallback_enabled": true
}
```

## 🚀 **PLAN DE IMPLEMENTACIÓN**

### **Fase 1: Infraestructura Base (Semana 1-2)**
- [ ] Crear tablas de base de datos
- [ ] Implementar gestor de configuración por tenant
- [ ] Crear sistema de webhooks central
- [ ] Implementar enrutamiento por tenant

### **Fase 2: Integración API Oficial (Semana 3-4)**
- [ ] Integrar WhatsApp Business API
- [ ] Implementar autenticación y tokens
- [ ] Crear sistema de plantillas
- [ ] Implementar envío de mensajes

### **Fase 3: Migración WhatsApp Web (Semana 5-6)**
- [ ] Adaptar sistema actual a multi-tenant
- [ ] Implementar aislamiento de sesiones
- [ ] Crear interfaz de configuración
- [ ] Migrar conversaciones existentes

### **Fase 4: Interfaz de Usuario (Semana 7-8)**
- [ ] Rediseñar pestaña de conversaciones
- [ ] Crear modal de configuración WhatsApp
- [ ] Implementar notificaciones en tiempo real
- [ ] Crear panel de administración

### **Fase 5: Funcionalidades Avanzadas (Semana 9-10)**
- [ ] Campañas masivas
- [ ] Plantillas dinámicas
- [ ] Reportes y analytics
- [ ] Integración con CRM (postulaciones, etc.)

## 🔧 **ENDPOINTS NUEVOS**

### **Configuración WhatsApp**
```python
# Configurar WhatsApp para un tenant
POST /api/whatsapp/config
{
  "api_type": "business_api",
  "business_api_token": "token...",
  "phone_number_id": "123456789012345"
}

# Obtener configuración actual
GET /api/whatsapp/config

# Probar conexión
POST /api/whatsapp/test-connection
```

### **Conversaciones**
```python
# Listar conversaciones del tenant
GET /api/whatsapp/conversations

# Obtener mensajes de una conversación
GET /api/whatsapp/conversations/{id}/messages

# Enviar mensaje
POST /api/whatsapp/conversations/{id}/messages
{
  "message": "Hola, ¿cómo estás?",
  "type": "text"
}
```

### **Webhooks**
```python
# Webhook para recibir mensajes de WhatsApp
POST /api/whatsapp/webhook
# (Maneja automáticamente el enrutamiento por tenant)

# Verificar webhook
GET /api/whatsapp/webhook?hub.mode=subscribe&hub.challenge=...
```

## 🎨 **INTERFAZ DE USUARIO**

### **Modal de Configuración WhatsApp**
```
┌─────────────────────────────────────────┐
│  📱 Configuración WhatsApp              │
├─────────────────────────────────────────┤
│                                         │
│  Tipo de Conexión:                     │
│  ○ WhatsApp Business API (Recomendado) │
│  ○ WhatsApp Web (Básico)               │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │ Configuración Business API          │ │
│  │                                     │ │
│  │ Token de Acceso: [________________] │ │
│  │ Phone Number ID: [________________] │ │
│  │                                     │ │
│  │ [🔗 Probar Conexión]               │ │
│  │                                     │ │
│  │ ✅ Conexión exitosa                 │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  [💾 Guardar Configuración]            │
│  [❌ Cancelar]                          │
│                                         │
└─────────────────────────────────────────┘
```

### **Nueva Pestaña de Conversaciones**
```
┌─────────────────────────────────────────────────────────┐
│  💬 Conversaciones                                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📊 Estado: ✅ Conectado via Business API              │
│  📱 Teléfono: +1 234 567 8901                         │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────────────────────┐ │
│  │ 📞 Contactos    │  │ 💬 Chat                         │ │
│  │                 │  │                                 │ │
│  │ 🔍 Juan Pérez   │  │ Juan Pérez                     │ │
│  │    Último msg   │  │ ┌─────────────────────────────┐ │ │
│  │                 │  │ │ Hola, ¿cómo estás?         │ │ │
│  │ 🔍 María García │  │ └─────────────────────────────┘ │ │
│  │    Último msg   │  │                                 │ │
│  │                 │  │ ┌─────────────────────────────┐ │ │
│  │ 🔍 Carlos López │  │ │ [Escribir mensaje...]      │ │ │
│  │    Último msg   │  │ └─────────────────────────────┘ │ │
│  └─────────────────┘  └─────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 📊 **BENEFICIOS DE LA NUEVA ARQUITECTURA**

### **Para el Sistema:**
- ✅ **Escalabilidad**: Cada tenant maneja su propia configuración
- ✅ **Confiabilidad**: Business API es más estable que Web
- ✅ **Flexibilidad**: Opción de usar Web como fallback
- ✅ **Seguridad**: Tokens y configuraciones aisladas por tenant

### **Para los Usuarios:**
- ✅ **Configuración Simple**: Modal intuitivo para configurar
- ✅ **Conversaciones Reales**: Interfaz como WhatsApp nativo
- ✅ **Notificaciones Automáticas**: Integradas con el CRM
- ✅ **Campañas Masivas**: Envío a listas de candidatos

### **Para el Negocio:**
- ✅ **Monetización**: Diferentes planes según tipo de API
- ✅ **Competitividad**: Funcionalidades empresariales
- ✅ **Retención**: Mejor experiencia de usuario
- ✅ **Escalabilidad**: Preparado para crecimiento

## 🔐 **CONSIDERACIONES DE SEGURIDAD**

### **Aislamiento por Tenant:**
- Cada tenant tiene sus propios tokens de API
- Webhooks enrutados automáticamente por tenant
- Base de datos completamente aislada
- No hay acceso cruzado entre tenants

### **Gestión de Tokens:**
- Tokens encriptados en base de datos
- Rotación automática de tokens
- Logs de acceso y uso
- Monitoreo de límites de API

### **Webhooks Seguros:**
- Verificación de firma de webhooks
- Rate limiting por tenant
- Validación de origen de mensajes
- Logs detallados de actividad

## 🎯 **PRÓXIMOS PASOS INMEDIATOS**

1. **Aprobar arquitectura propuesta**
2. **Crear tablas de base de datos**
3. **Implementar gestor de configuración**
4. **Crear sistema de webhooks**
5. **Desarrollar interfaz de configuración**

¿Te parece bien esta arquitectura? ¿Hay algún aspecto que quieras modificar o profundizar?
