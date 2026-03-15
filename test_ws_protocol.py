# -*- coding: utf-8 -*-
import os
import json
import logging
import websocket
from flask import jsonify, request, g
from functools import wraps

# Configurar logger
logger = logging.getLogger(__name__)

def token_required(f):
    """Placeholder para mantener compatibilidad si se mueve a archivo separado"""
    return f

def proxy_agent_chat_ws():
    """
    Proxy de comunicación nativa vía WebSocket.
    Elimina la necesidad de habilitar APIs REST (HTTP) en OpenClaw,
    usando el protocolo nativo del Gateway.
    """
    tenant_id = getattr(g, 'current_tenant_id', 1)
    data = request.get_json()
    message = data.get('message')

    if not message:
        return jsonify({"error": "Mensaje requerido"}), 400

    # Dirección interna del Docker mapeada en la VM
    ws_url = f"ws://127.0.0.1:{19000 + tenant_id}"
    token = "esc-agent-token-secure-v2"
    
    logger.info(f"Iniciando túnel WebSocket nativo hacia: {ws_url}")
    
    try:
        # 1. Abrir conexión al Gateway de OpenClaw
        ws = websocket.create_connection(ws_url, timeout=30)
        
        # 2. Protocolo de Identificación (Auth)
        ws.send(json.dumps({
            "type": "auth",
            "token": token
        }))
        
        # 3. Protocolo de Ejecución (Agent Turn)
        ws.send(json.dumps({
            "type": "agent",
            "agentId": "main",
            "message": message,
            "sessionKey": f"crm-session-{tenant_id}"
        }))
        
        # 4. Recolector de flujo de respuesta
        bot_text = ""
        while True:
            raw_msg = ws.recv()
            if not raw_msg: break
            
            event = json.loads(raw_msg)
            event_type = event.get("type")
            
            # Acumular texto conforme llega
            if event_type == "text":
                bot_text += event.get("text", "")
            
            # Finalizar si el agente terminó o hubo error
            if event_type in ["done", "stop", "error"]:
                if event_type == "error":
                    logger.error(f"Error en motor de agente: {event.get('text')}")
                    return jsonify({"error": event.get("text")}), 500
                break
        
        ws.close()
        return jsonify({"response": bot_text.strip()}), 200

    except Exception as e:
        logger.error(f"Fallo en túnel WebSocket: {str(e)}")
        return jsonify({"error": "No se pudo establecer comunicación nativa con el motor."}), 503
