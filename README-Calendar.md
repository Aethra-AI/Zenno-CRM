# 📅 Sistema de Calendario - Zenno CRM

## Descripción General

El sistema de calendario del Zenno CRM permite a los usuarios gestionar recordatorios, visualizar entrevistas programadas y realizar seguimiento de actividades diarias. Está diseñado para facilitar la organización y coordinación del equipo de reclutamiento.

## 🚀 Características Principales

### 1. **Recordatorios**
- **Personales**: Solo visibles para el usuario que los crea
- **Equipo**: Visibles para todos los miembros del equipo del tenant
- **Generales**: Visibles para todos los usuarios del sistema (solo admin/supervisor)

### 2. **Entrevistas**
- Integración automática con el sistema de entrevistas existente
- Visualización de candidatos, vacantes y horarios
- Estados: programada, completada, cancelada, reprogramada

### 3. **Actividades Diarias**
- Seguimiento automático de postulaciones
- Registro de entrevistas programadas
- Estadísticas de contrataciones y rechazos

### 4. **Interfaz Responsiva**
- Vista de calendario mensual
- Modal detallado para eventos del día
- Filtros por tipo de evento
- Búsqueda de eventos

## 🗄️ Estructura de Base de Datos

### Tabla: `calendar_reminders`
```sql
CREATE TABLE calendar_reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    date DATE NOT NULL,
    time TIME NOT NULL,
    type ENUM('personal', 'team', 'general') NOT NULL DEFAULT 'personal',
    priority ENUM('low', 'medium', 'high') NOT NULL DEFAULT 'medium',
    status ENUM('pending', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
    created_by INT NOT NULL,
    assigned_to JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Tabla: `interviews`
```sql
CREATE TABLE interviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    candidate_id INT NOT NULL,
    vacancy_id INT NOT NULL,
    interview_date DATE NOT NULL,
    interview_time TIME NOT NULL,
    status ENUM('scheduled', 'completed', 'cancelled', 'rescheduled') NOT NULL DEFAULT 'scheduled',
    notes TEXT,
    interviewer VARCHAR(255),
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 🔌 Endpoints API

### Recordatorios

#### `GET /api/calendar/reminders`
Obtener recordatorios del mes
- **Query params**: `year`, `month`
- **Response**: Lista de recordatorios

#### `POST /api/calendar/reminders`
Crear nuevo recordatorio
- **Body**: 
  ```json
  {
    "title": "string",
    "description": "string",
    "date": "YYYY-MM-DD",
    "time": "HH:MM:SS",
    "type": "personal|team|general",
    "priority": "low|medium|high",
    "assigned_to": ["user_id1", "user_id2"]
  }
  ```

#### `PUT /api/calendar/reminders/{id}`
Actualizar recordatorio existente
- **Body**: Mismos campos que POST

#### `DELETE /api/calendar/reminders/{id}`
Eliminar recordatorio

### Entrevistas

#### `GET /api/calendar/interviews`
Obtener entrevistas del mes
- **Query params**: `year`, `month`
- **Response**: Lista de entrevistas con información de candidatos y vacantes

### Actividades

#### `GET /api/calendar/activities`
Obtener actividades del mes
- **Query params**: `year`, `month`
- **Response**: Lista de actividades (postulaciones, entrevistas, etc.)

## 🎨 Componentes Frontend

### `Calendar.tsx`
Componente principal del calendario
- Vista mensual con navegación
- Modal de eventos del día
- Formulario para crear recordatorios

### `DailyActivitySummary.tsx`
Resumen de actividades diarias
- Estadísticas de postulaciones, entrevistas, etc.
- Indicadores visuales por tipo de actividad

### `CalendarStats.tsx`
Estadísticas generales del calendario
- Tasa de completación
- Contadores por tipo de evento

## 🔐 Permisos y Seguridad

### Roles y Permisos
- **Usuario**: Solo puede crear/modificar recordatorios personales
- **Supervisor**: Puede crear recordatorios de equipo y ver todos los del tenant
- **Admin**: Puede crear recordatorios generales y ver todos los del sistema

### Multi-tenancy
- Todos los endpoints respetan el `tenant_id`
- Los datos están aislados por tenant
- Solo los usuarios del mismo tenant pueden ver los recordatorios de equipo

## 🚀 Instalación y Configuración

### 1. Crear las tablas
```bash
python create_calendar_tables.py
```

### 2. Verificar endpoints
```bash
python test_calendar_endpoints.py
```

### 3. Acceder al calendario
- URL: `http://localhost:8080/calendar`
- Requiere autenticación

## 📊 Uso del Sistema

### Para Usuarios
1. **Crear recordatorio personal**:
   - Click en "Nuevo Recordatorio"
   - Seleccionar tipo "Personal"
   - Configurar fecha, hora y prioridad

2. **Ver entrevistas del día**:
   - Click en cualquier día del calendario
   - Revisar lista de entrevistas programadas

3. **Filtrar eventos**:
   - Usar filtros en la parte superior
   - Buscar eventos específicos

### Para Supervisores/Admins
1. **Crear recordatorios de equipo**:
   - Seleccionar tipo "Equipo" o "General"
   - Asignar a usuarios específicos

2. **Monitorear actividades**:
   - Revisar estadísticas del equipo
   - Ver tasa de completación

## 🔧 Personalización

### Agregar nuevos tipos de eventos
1. Modificar enum en la base de datos
2. Actualizar frontend para mostrar el nuevo tipo
3. Agregar lógica de permisos si es necesario

### Integrar con otros sistemas
- Los endpoints están diseñados para ser extensibles
- Se puede agregar integración con Google Calendar, Outlook, etc.
- Webhooks para notificaciones externas

## 🐛 Solución de Problemas

### Error: "Tabla no encontrada"
```bash
python create_calendar_tables.py
```

### Error: "Permisos insuficientes"
- Verificar que el usuario tenga el rol correcto
- Comprobar que el recordatorio pertenezca al tenant del usuario

### Error: "Token inválido"
- Verificar que el usuario esté autenticado
- Comprobar que el token no haya expirado

## 📈 Métricas y Analytics

El sistema registra automáticamente:
- Número de recordatorios por usuario/equipo
- Tasa de completación de recordatorios
- Actividades diarias del equipo
- Tendencias de entrevistas y contrataciones

## 🔮 Futuras Mejoras

- [ ] Notificaciones push para recordatorios
- [ ] Integración con calendarios externos
- [ ] Reportes automáticos por email
- [ ] IA para sugerir horarios de entrevistas
- [ ] Sincronización con dispositivos móviles

