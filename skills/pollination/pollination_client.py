import os
import requests
import json
import logging

logger = logging.getLogger(__name__)

class PollinationSkill:
    """
    Skill para generar imágenes usando Pollinations.ai.
    """
    
    def __init__(self):
        self.base_url = "https://image.pollinations.ai/prompt/"
        
    def generate_image(self, prompt, width=1024, height=1024, model="flux"):
        """
        Genera una imagen basada en un prompt.
        Retorna la URL de la imagen generada.
        """
        if not prompt:
            return {"error": "Se requiere un prompt para generar la imagen"}
            
        # Limpiar y codificar el prompt para la URL
        prompt_encoded = requests.utils.quote(prompt)
        
        # Construir URL con parámetros
        # Pollinations permite parámetros como ?width=X&height=Y&model=flux&nologo=true
        image_url = f"{self.base_url}{prompt_encoded}?width={width}&height={height}&model={model}&nologo=true&seed={os.urandom(4).hex()}"
        
        logger.info(f"Imagen solicitada a Pollinations: {prompt[:50]}...")
        
        # En Pollinations, la URL en sí misma sirve como el 'endpoint' de la imagen.
        # Podemos verificar si es accesible o simplemente retornar la URL.
        return {
            "success": True,
            "image_url": image_url,
            "prompt": prompt,
            "message": "Imagen generada exitosamente. Puedes verla en el enlace adjunto."
        }

# Instancia para uso del agente
pollination = PollinationSkill()
