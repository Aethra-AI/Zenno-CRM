# 📱 PLAN DE MIGRACIÓN GRADUAL: WHATSAPP MULTI-TENANT

## 🎯 **OBJETIVO DE LA MIGRACIÓN**

Transformar el sistema actual de WhatsApp Web.js hacia una arquitectura multi-tenant que soporte tanto WhatsApp Business API como WhatsApp Web, manteniendo la funcionalidad existente mientras se implementan las nuevas características.

## 📋 **ESTRATEGIA DE MIGRACIÓN**

### **Principios de la Migración:**
- ✅ **Migración Gradual**: Sin interrupciones del servicio
- ✅ **Compatibilidad**: Mantener funcionalidad existente
- ✅ **Aislamiento**: Cada tenant independiente
- ✅ **Rollback**: Posibilidad de revertir cambios
- ✅ **Testing**: Validación en cada fase

## 🗓️ **CRONOGRAMA DETALLADO**

### **FASE 1: PREPARACIÓN E INFRAESTRUCTURA (Semana 1-2)**

#### **Semana 1: Base de Datos y Configuración**
```bash
# Día 1-2: Crear esquema de base de datos
- [ ] Ejecutar whatsapp_database_schema.sql
- [ ] Crear tablas de configuración
- [ ] Configurar índices y triggers
- [ ] Insertar datos iniciales

# Día 3-4: Configuración de entorno
- [ ] Instalar dependencias (Celery, Redis)
- [ ] Configurar variables de entorno
- [ ] Crear estructura de directorios
- [ ] Configurar logging

# Día 5: Testing de infraestructura
- [ ] Probar conexiones de BD
- [ ] Verificar configuración Celery
- [ ] Test de conectividad Redis
```

#### **Semana 2: Módulos Base**
```bash
# Día 1-3: Implementar gestores base
- [ ] WhatsAppWebhookRouter
- [ ] WhatsAppBusinessAPIManager
- [ ] WhatsAppWebManager (adaptado)

# Día 4-5: Testing de módulos
- [ ] Unit tests para cada módulo
- [ ] Integration tests
- [ ] Error handling tests
```

### **FASE 2: INTEGRACIÓN API OFICIAL (Semana 3-4)**

#### **Semana 3: WhatsApp Business API**
```bash
# Día 1-2: Configuración de API
- [ ] Implementar autenticación
- [ ] Configurar webhooks
- [ ] Crear sistema de plantillas

# Día 3-4: Funcionalidades core
- [ ] Envío de mensajes de texto
- [ ] Envío de mensajes de plantilla
- [ ] Manejo de multimedia

# Día 5: Testing API
- [ ] Probar conexión con API real
- [ ] Test de envío de mensajes
- [ ] Validar webhooks
```

#### **Semana 4: Sistema Multi-Tenant**
```bash
# Día 1-2: Aislamiento por tenant
- [ ] Implementar routing por tenant
- [ ] Configurar tokens individuales
- [ ] Aislamiento de datos

# Día 3-4: Gestión de configuración
- [ ] Panel de configuración por tenant
- [ ] Validación de tokens
- [ ] Manejo de errores por tenant

# Día 5: Testing multi-tenant
- [ ] Probar aislamiento
- [ ] Test de configuración
- [ ] Validar seguridad
```

### **FASE 3: MIGRACIÓN WHATSAPP WEB (Semana 5-6)**

#### **Semana 5: Adaptación del Sistema Actual**
```bash
# Día 1-2: Refactorizar bridge.js
- [ ] Adaptar a multi-tenant
- [ ] Aislamiento de sesiones
- [ ] Gestión de configuraciones

# Día 3-4: Migrar endpoints
- [ ] Actualizar rutas de API
- [ ] Adaptar WebSocket
- [ ] Migrar conversaciones

# Día 5: Testing migración
- [ ] Probar funcionalidad existente
- [ ] Validar aislamiento
- [ ] Test de performance
```

#### **Semana 6: Interfaz de Usuario**
```bash
# Día 1-2: Modal de configuración
- [ ] Diseñar interfaz
- [ ] Implementar configuración API
- [ ] Implementar configuración Web

# Día 3-4: Nueva pestaña de conversaciones
- [ ] Rediseñar interfaz
- [ ] Implementar conversaciones reales
- [ ] Integrar notificaciones

# Día 5: Testing UI
- [ ] Probar interfaz completa
- [ ] Validar UX
- [ ] Test de responsividad
```

### **FASE 4: FUNCIONALIDADES AVANZADAS (Semana 7-8)**

#### **Semana 7: Notificaciones Automáticas**
```bash
# Día 1-2: Sistema de plantillas
- [ ] Crear plantillas dinámicas
- [ ] Sistema de variables
- [ ] Gestión de plantillas

# Día 3-4: Notificaciones automáticas
- [ ] Triggers de eventos
- [ ] Envío automático
- [ ] Logs de notificaciones

# Día 5: Testing notificaciones
- [ ] Probar triggers
- [ ] Validar envío
- [ ] Test de logs
```

#### **Semana 8: Campañas y Reportes**
```bash
# Día 1-2: Campañas masivas
- [ ] Sistema de campañas
- [ ] Envío masivo
- [ ] Tracking de resultados

# Día 3-4: Reportes y analytics
- [ ] Dashboard de estadísticas
- [ ] Reportes de uso
- [ ] Métricas de performance

# Día 5: Testing final
- [ ] Pruebas integrales
- [ ] Performance testing
- [ ] Security testing
```

## 🔄 **PROCESO DE MIGRACIÓN DETALLADO**

### **1. PREPARACIÓN DEL ENTORNO**

#### **Backup y Seguridad**
```bash
# 1. Backup completo de base de datos
mysqldump -u root -p crm_db > backup_pre_migration.sql

# 2. Backup de archivos de configuración
cp -r bACKEND/config bACKEND/config_backup
cp -r zenno-canvas-flow-main/src zenno-canvas-flow-main/src_backup

# 3. Crear rama de migración en Git
git checkout -b feature/whatsapp-migration
git add .
git commit -m "Backup pre-migración WhatsApp"
```

#### **Instalación de Dependencias**
```bash
# Backend
pip install celery redis requests python-dotenv

# Frontend (si es necesario)
npm install socket.io-client
```

### **2. IMPLEMENTACIÓN GRADUAL**

#### **Paso 1: Crear Tablas de Base de Datos**
```sql
-- Ejecutar en MySQL
SOURCE whatsapp_database_schema.sql;

-- Verificar creación
SHOW TABLES LIKE 'WhatsApp_%';
```

#### **Paso 2: Implementar Módulos Base**
```python
# 1. Crear archivo de configuración
# whatsapp_config.py

# 2. Implementar gestores
# whatsapp_webhook_router.py
# whatsapp_business_api_manager.py

# 3. Integrar con app.py
```

#### **Paso 3: Configuración por Tenant**
```python
# Endpoint para configurar WhatsApp por tenant
@app.route('/api/whatsapp/config', methods=['GET', 'POST', 'PUT'])
@token_required
def whatsapp_config():
    tenant_id = get_current_tenant_id()
    
    if request.method == 'GET':
        # Obtener configuración actual
        pass
    elif request.method == 'POST':
        # Crear nueva configuración
        pass
    elif request.method == 'PUT':
        # Actualizar configuración
        pass
```

### **3. MIGRACIÓN DE DATOS EXISTENTES**

#### **Script de Migración de Conversaciones**
```python
# migrate_existing_conversations.py
def migrate_existing_data():
    """
    Migrar conversaciones existentes del sistema actual
    """
    # 1. Obtener conversaciones existentes
    # 2. Crear nuevas conversaciones con tenant_id
    # 3. Migrar mensajes
    # 4. Actualizar referencias
    pass
```

#### **Migración de Configuraciones**
```python
# migrate_whatsapp_configs.py
def migrate_tenant_configs():
    """
    Migrar configuraciones de WhatsApp por tenant
    """
    # 1. Obtener configuraciones actuales
    # 2. Crear registros en WhatsApp_Config
    # 3. Asignar tenant_id
    # 4. Validar configuraciones
    pass
```

### **4. TESTING Y VALIDACIÓN**

#### **Test Suite Completo**
```python
# tests/test_whatsapp_migration.py
class TestWhatsAppMigration:
    def test_tenant_isolation(self):
        """Probar aislamiento por tenant"""
        pass
    
    def test_api_integration(self):
        """Probar integración con API"""
        pass
    
    def test_webhook_routing(self):
        """Probar routing de webhooks"""
        pass
    
    def test_message_flow(self):
        """Probar flujo completo de mensajes"""
        pass
```

#### **Validación de Performance**
```bash
# Test de carga
ab -n 1000 -c 10 http://localhost:5000/api/whatsapp/webhook

# Test de memoria
python -m memory_profiler whatsapp_webhook_router.py

# Test de concurrencia
python test_concurrent_tenants.py
```

## 🚨 **PLAN DE ROLLBACK**

### **Escenarios de Rollback**

#### **Rollback Parcial (Fase 1-2)**
```bash
# 1. Desactivar nuevas funcionalidades
UPDATE WhatsApp_Config SET is_active = FALSE WHERE api_type = 'business_api';

# 2. Revertir cambios en app.py
git checkout HEAD~1 -- app.py

# 3. Reiniciar servicios
sudo systemctl restart crm-backend
```

#### **Rollback Completo**
```bash
# 1. Restaurar backup de BD
mysql -u root -p crm_db < backup_pre_migration.sql

# 2. Revertir código
git checkout main
git branch -D feature/whatsapp-migration

# 3. Restaurar archivos de configuración
cp -r bACKEND/config_backup/* bACKEND/config/
```

### **Indicadores de Rollback**
- ❌ **Error rate > 5%** en nuevos endpoints
- ❌ **Response time > 2s** en operaciones críticas
- ❌ **Memory usage > 80%** del servidor
- ❌ **Database locks** frecuentes
- ❌ **WebSocket disconnections** masivas

## 📊 **MÉTRICAS DE ÉXITO**

### **Métricas Técnicas**
- ✅ **Uptime**: > 99.9%
- ✅ **Response Time**: < 500ms promedio
- ✅ **Error Rate**: < 1%
- ✅ **Memory Usage**: < 70%
- ✅ **Database Performance**: < 100ms por query

### **Métricas de Negocio**
- ✅ **Adoption Rate**: > 80% de tenants migrados
- ✅ **User Satisfaction**: > 4.5/5
- ✅ **Feature Usage**: > 60% usa nuevas funcionalidades
- ✅ **Support Tickets**: < 5 por semana
- ✅ **Performance Improvement**: > 30% en velocidad

## 🔧 **HERRAMIENTAS DE MONITOREO**

### **Logging y Monitoreo**
```python
# Configurar logging detallado
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_migration.log'),
        logging.StreamHandler()
    ]
)
```

### **Métricas en Tiempo Real**
```python
# Dashboard de métricas
@app.route('/api/whatsapp/metrics')
@token_required
def whatsapp_metrics():
    return jsonify({
        'active_tenants': get_active_tenants_count(),
        'messages_sent_today': get_messages_sent_today(),
        'api_usage': get_api_usage_stats(),
        'error_rate': get_error_rate()
    })
```

## 📝 **CHECKLIST DE MIGRACIÓN**

### **Pre-Migración**
- [ ] Backup completo de BD
- [ ] Backup de archivos de configuración
- [ ] Crear rama de migración en Git
- [ ] Instalar dependencias necesarias
- [ ] Configurar entorno de testing
- [ ] Documentar estado actual

### **Durante la Migración**
- [ ] Ejecutar scripts de BD paso a paso
- [ ] Implementar módulos uno por uno
- [ ] Testing después de cada cambio
- [ ] Monitoreo continuo de métricas
- [ ] Documentar cambios realizados
- [ ] Comunicar progreso al equipo

### **Post-Migración**
- [ ] Validación completa del sistema
- [ ] Testing de performance
- [ ] Testing de seguridad
- [ ] Documentación actualizada
- [ ] Capacitación del equipo
- [ ] Plan de soporte activado

## 🎯 **PRÓXIMOS PASOS INMEDIATOS**

### **Semana Actual**
1. **Aprobar plan de migración**
2. **Preparar entorno de desarrollo**
3. **Crear backup de seguridad**
4. **Instalar dependencias**
5. **Iniciar Fase 1**

### **Decisiones Pendientes**
- [ ] **Confirmar cronograma** con el equipo
- [ ] **Asignar recursos** para cada fase
- [ ] **Definir criterios de éxito** específicos
- [ ] **Establecer comunicación** durante la migración
- [ ] **Preparar plan de capacitación** para usuarios

## 📞 **CONTACTO Y SOPORTE**

### **Durante la Migración**
- **Lead Developer**: Responsable técnico
- **DevOps**: Infraestructura y despliegue
- **QA**: Testing y validación
- **Product Manager**: Validación de funcionalidades

### **Canal de Comunicación**
- **Slack**: #whatsapp-migration
- **Email**: migration-team@company.com
- **Meetings**: Daily standup a las 9:00 AM
- **Reports**: Weekly progress report los viernes

---

**¿Estás listo para comenzar la migración? ¿Hay algún aspecto del plan que quieras modificar o profundizar?**
