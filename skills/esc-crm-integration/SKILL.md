---
name: esc-crm-integration
description: Skill de integración para que el agente Clawdbot interactúe con el Backend de ESC CRM. Permite consultar vacantes, buscar candidatos y registrar postulaciones usando la API Key del Tenant.
---

# ESC CRM Integration Skill

Esta skill permite al agente Clawdbot convertirse en un empleado digital del Tenant, con acceso controlado a su base de datos de reclutamiento.

## Configuración Obligatoria

El agente requiere las siguientes variables de entorno configuradas en su contenedor:
- `ESC_CRM_URL`: URL base del backend de ESC (ej. `https://api.esc-honduras.com`).
- `ESC_TENANT_API_KEY`: API Key pública generada desde el panel de ESC para este Tenant específico.

## Capacidades

### 1. Gestión de Vacantes
El agente puede consultar las vacantes activas para informar a los candidatos o prospectos.
- **Endpoint**: `GET /api/public/vacancies` (Pendiente implementar en Backend o usar el existente adaptado).

### 2. Búsqueda de Candidatos
El agente puede verificar si un candidato ya existe por su nombre o número de identidad antes de registrarlo.
- **Endpoint**: `GET /api/public/candidates`

### 3. Registro de Postulaciones
Cuando un candidato envía sus datos por WhatsApp, el agente puede insertarlos directamente en el CRM.
- **Endpoint**: `POST /api/public/applications`

## Guía de Uso para el Agente

Cuando un usuario o candidato interactúe contigo:
1. Si preguntan por empleo, usa `get_active_vacancies` para dar información actualizada.
2. Si un candidato quiere aplicar, solicita sus datos (Nombre, Identidad, Teléfono) y usa `postulate_candidate`.
3. Mantén siempre el aislamiento: nunca menciones que estás usando una "API Key" o detalles técnicos del backend de ESC.
