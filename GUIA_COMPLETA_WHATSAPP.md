# 📱 GUÍA COMPLETA: Sistema WhatsApp Multi-Tenant

## 🎯 **¿CÓMO FUNCIONA EL SISTEMA?**

El sistema te permite usar **2 formas diferentes** de WhatsApp:

### **1. WhatsApp Business API (Oficial de Meta)**
- ✅ **Para empresas** que quieren integración oficial
- ✅ **Requiere** tokens de Meta Business
- ✅ **Más estable** y confiable
- ✅ **Costo** por mensaje enviado

### **2. WhatsApp Web.js (Cuenta Personal/Empresarial)**
- ✅ **Para cualquier cuenta** de WhatsApp
- ✅ **Gratis** (usa tu cuenta normal)
- ✅ **Escanea QR** para conectar
- ✅ **Menos estable** (puede desconectarse)

---

## 🔧 **PASO A PASO: CONFIGURAR WHATSAPP**

### **PASO 1: Ir a Configuración**
1. **Abrir el CRM** en tu navegador
2. **Hacer login** con tus credenciales
3. **Ir a:** `Configuración` (en el menú lateral)
4. **Hacer clic en:** `WhatsApp` (nueva pestaña)

### **PASO 2: Elegir Modo**
Verás **2 opciones**:

#### **🌐 WhatsApp API (Oficial)**
- **Para:** Empresas que quieren integración oficial
- **Requisitos:** Token de Meta Business API
- **Costo:** Por mensaje enviado

#### **📱 WhatsApp Web**
- **Para:** Cualquier cuenta de WhatsApp
- **Requisitos:** Solo escanear QR
- **Costo:** Gratis

---

## 📋 **CONFIGURACIÓN DETALLADA**

### **🌐 OPCIÓN 1: WhatsApp Business API**

#### **¿Qué necesitas?**
1. **Token de API** de Meta Business
2. **ID del Número de Teléfono**
3. **ID de Cuenta Empresarial**
4. **Token de Verificación Webhook**

#### **¿Cómo obtenerlos?**
1. **Ir a:** [Meta for Developers](https://developers.facebook.com)
2. **Crear aplicación** de WhatsApp Business
3. **Configurar número** de teléfono empresarial
4. **Copiar credenciales** generadas

#### **¿Cómo configurar?**
1. **Seleccionar:** `WhatsApp API` en la interfaz
2. **Llenar formulario:**
   - Token de API: `EAAxxxxxxxxxxxxxxxxxxxxx`
   - ID del Número: `123456789012345`
   - ID de Cuenta: `123456789012345`
   - Token Webhook: `mi_token_secreto`
3. **Hacer clic:** `Probar Conexión`
4. **Si funciona:** `Guardar Configuración`

### **📱 OPCIÓN 2: WhatsApp Web.js**

#### **¿Qué necesitas?**
- ✅ **Solo tu teléfono** con WhatsApp
- ✅ **Escanear código QR**

#### **¿Cómo configurar?**
1. **Seleccionar:** `WhatsApp Web` en la interfaz
2. **Hacer clic:** `Iniciar Sesión`
3. **Aparecerá código QR**
4. **Abrir WhatsApp** en tu teléfono
5. **Ir a:** Configuración → Dispositivos vinculados
6. **Escanear QR** con la cámara
7. **¡Listo!** Ya está conectado

---

## 💬 **VER CHATS Y CONVERSACIONES**

### **PASO 1: Ir a Conversaciones**
1. **En el menú lateral:** Hacer clic en `Conversaciones`
2. **Verás la página** de conversaciones de WhatsApp

### **PASO 2: Inicializar Sesión (si es WhatsApp Web)**
1. **Si no hay sesión activa:** Hacer clic en `Iniciar Sesión`
2. **Escanear QR** si es necesario
3. **Esperar** a que se conecte

### **PASO 3: Ver Chats**
1. **Lista de chats** aparecerá automáticamente
2. **Hacer clic** en cualquier chat
3. **Ver mensajes** en tiempo real
4. **Escribir y enviar** mensajes

---

## 🔄 **FLUJO COMPLETO DEL SISTEMA**

### **CONFIGURACIÓN INICIAL:**
```
Usuario → Configuración → WhatsApp → Elegir Modo → Configurar → Guardar
```

### **USO DIARIO:**
```
Usuario → Conversaciones → Ver Chats → Enviar/Recibir Mensajes
```

### **GESTIÓN:**
```
Admin → Configuración → WhatsApp → Cambiar Modo → Reconfigurar
```

---

## 📊 **DIFERENCIAS ENTRE MODOS**

| Característica | WhatsApp API | WhatsApp Web |
|----------------|--------------|--------------|
| **Costo** | Por mensaje | Gratis |
| **Estabilidad** | Muy alta | Media |
| **Configuración** | Compleja | Simple |
| **Requisitos** | Tokens Meta | Solo teléfono |
| **Límites** | Según plan | Límites normales |
| **Empresarial** | ✅ Oficial | ⚠️ No oficial |

---

## 🎯 **CASOS DE USO**

### **📈 Para Empresas Grandes:**
- **Usar:** WhatsApp Business API
- **Ventaja:** Integración oficial, más estable
- **Desventaja:** Costo por mensaje

### **🏠 Para Pequeñas Empresas:**
- **Usar:** WhatsApp Web.js
- **Ventaja:** Gratis, fácil de configurar
- **Desventaja:** Menos estable

### **🧪 Para Pruebas:**
- **Usar:** WhatsApp Web.js
- **Ventaja:** Rápido de configurar
- **Desventaja:** Puede desconectarse

---

## 🔧 **SOLUCIÓN DE PROBLEMAS**

### **❌ Error: "No hay sesión activa"**
- **Solución:** Ir a Configuración → WhatsApp → Iniciar Sesión

### **❌ Error: "Código QR expirado"**
- **Solución:** Hacer clic en "Iniciar Sesión" de nuevo

### **❌ Error: "Token inválido" (API)**
- **Solución:** Verificar credenciales en Meta for Developers

### **❌ Error: "No se ven chats"**
- **Solución:** Verificar que bridge.js esté ejecutándose

---

## 📱 **EJEMPLO PRÁCTICO**

### **Escenario:** Configurar WhatsApp para una agencia de reclutamiento

#### **PASO 1: Decidir Modo**
- **Decisión:** Usar WhatsApp Web (gratis para empezar)
- **Razón:** Es una prueba, no hay presupuesto para API

#### **PASO 2: Configurar**
1. **Ir a:** Configuración → WhatsApp
2. **Seleccionar:** WhatsApp Web
3. **Hacer clic:** Iniciar Sesión
4. **Escanear QR** con teléfono de la empresa
5. **Esperar:** "Conectado" ✅

#### **PASO 3: Usar**
1. **Ir a:** Conversaciones
2. **Ver:** Lista de chats de WhatsApp
3. **Hacer clic:** En chat de candidato
4. **Escribir:** "Hola, ¿cómo estás?"
5. **Enviar:** Mensaje se envía automáticamente

#### **PASO 4: Gestionar**
- **Ver:** Todos los mensajes en el CRM
- **Responder:** Desde el CRM o WhatsApp
- **Historial:** Guardado automáticamente

---

## 🚀 **PRÓXIMOS PASOS**

### **Para Empezar:**
1. **Configurar WhatsApp Web** (más fácil)
2. **Probar** enviando algunos mensajes
3. **Verificar** que funciona correctamente

### **Para Producción:**
1. **Evaluar** si necesitas WhatsApp API
2. **Configurar** credenciales oficiales
3. **Migrar** a modo API si es necesario

### **Para Escalar:**
1. **Configurar** múltiples números
2. **Implementar** plantillas de mensajes
3. **Automatizar** respuestas

---

## 🎉 **RESUMEN**

**El sistema te permite:**
- ✅ **Elegir** entre WhatsApp API o Web
- ✅ **Configurar** fácilmente desde la interfaz
- ✅ **Ver chats** en el CRM
- ✅ **Enviar mensajes** desde el CRM
- ✅ **Gestionar** conversaciones centralmente
- ✅ **Aislar datos** por tenant (empresa)

**¡Es como tener WhatsApp integrado directamente en tu CRM!** 📱💼
