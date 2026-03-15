---
name: pollination
description: Skill para generación de imágenes de alta calidad usando Pollinations.ai. Permite al agente crear contenido visual a partir de descripciones de texto.
---

# Pollination Image Generation Skill

Esta skill permite al agente OpenClaw generar imágenes dinámicas.

## Capacidades

### 1. Generación de Imágenes
El agente puede crear imágenes profesionales para marketing, prototipos o asistencia visual.
- **Función**: `generate_image(prompt)`
- **Modelos soportados**: flux (por defecto), turbo.

## Guía de Uso para el Agente

Cuando un usuario te pida crear una imagen o algo visual:
1. Pide detalles específicos sobre la imagen si el prompt es muy vago.
2. Usa la función `generate_image` con un prompt descriptivo (preferiblemente en inglés para mejores resultados con el modelo).
3. Muestra el enlace resultante al usuario de forma amigable.

Ejemplo de prompt interno: "A futuristic office building with digital screens, cinematic lighting, 8k resolution"
