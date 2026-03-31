# -*- coding: utf-8 -*-
import json
import logging
import websocket
import sys

# Configurar logging básico para ver qué pasa
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_test():
    """
    Prueba de comunicación directa con el Gateway de OpenClaw vía WebSocket.
    """
    tenant_id = 1
    message = "Hola, ¿estás operativo?"
    ws_url = f"ws://127.0.0.1:{19000 + tenant_id}"
    token = "esc-agent-token-secure-v2"
    
    logger.info(f"🚀 Iniciando prueba de túnel WebSocket nativo hacia: {ws_url}")
    
    try:
        # 1. Abrir conexión al Gateway de OpenClaw
        ws = websocket.create_connection(ws_url, timeout=15)
        logger.info("✅ Conexión establecida con el servidor.")
        
        # 2. Protocolo de Identificación (Auth)
        auth_payload = {
            "type": "auth",
            "token": token
        }
        logger.info(f"🔑 Enviando payload de autenticación: {json.dumps(auth_payload)}")
        ws.send(json.dumps(auth_payload))
        
        # 3. Protocolo de Ejecución (Agent Turn)
        agent_payload = {
            "type": "agent",
            "agentId": "main",
            "message": message,
            "sessionKey": f"crm-session-test-{tenant_id}"
        }
        logger.info(f"📤 Enviando mensaje del agente: {json.dumps(agent_payload)}")
        ws.send(json.dumps(agent_payload))
        
        # 4. Recolector de flujo de respuesta
        logger.info("📥 Esperando respuesta del Gateway...")
        bot_text = ""
        while True:
            try:
                raw_msg = ws.recv()
                if not raw_msg: 
                    logger.warning("⚠️ El servidor cerró la conexión sin enviar 'done'.")
                    break
                
                event = json.loads(raw_msg)
                event_type = event.get("type")
                logger.info(f"📦 Evento recibido: {event_type}")
                
                # Acumular texto conforme llega
                if event_type == "text":
                    chunk = event.get("text", "")
                    bot_text += chunk
                    print(chunk, end="", flush=True)
                
                # Finalizar si el agente terminó o hubo error
                if event_type in ["done", "stop", "error"]:
                    if event_type == "error":
                        logger.error(f"❌ Error en motor de agente: {event.get('text')}")
                    else:
                        logger.info(f"\n✅ Respuesta completada exitosamente.")
                    break
            except Exception as e:
                logger.error(f"❌ Error durante la recepción: {str(e)}")
                break
        
        ws.close()
        print(f"\n\nRespuesta final acumulada: {bot_text.strip()}")
        return True

    except ConnectionRefusedError:
        logger.error(f"❌ Conexión rechazada en {ws_url}. ¿Está el Gateway corriendo?")
        return False
    except Exception as e:
        logger.error(f"❌ Fallo crítico en túnel WebSocket: {str(e)}")
        return False

if __name__ == "__main__":
    run_test()
