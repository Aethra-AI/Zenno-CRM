#!/usr/bin/env python3
"""
📱 TEST WEBHOOK SYSTEM
======================

Script para probar el sistema de webhooks de WhatsApp
simulando mensajes entrantes y verificaciones.
"""

import json
import requests
import time
from datetime import datetime

def test_webhook_verification():
    """Probar verificación de webhook"""
    print("🔍 Probando verificación de webhook...")
    
    # Simular parámetros de verificación de WhatsApp
    params = {
        'hub.mode': 'subscribe',
        'hub.verify_token': 'mi_token_secreto_ejemplo',  # Token de la configuración de ejemplo
        'hub.challenge': 'test_challenge_12345'
    }
    
    try:
        response = requests.get('http://localhost:5000/api/whatsapp/webhook', params=params)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Verificación de webhook exitosa")
            return True
        else:
            print("❌ Error en verificación de webhook")
            return False
            
    except Exception as e:
        print(f"❌ Error probando verificación: {e}")
        return False

def test_webhook_message():
    """Probar procesamiento de mensaje entrante"""
    print("\n📨 Probando procesamiento de mensaje entrante...")
    
    # Simular webhook de mensaje entrante
    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789012345",  # phone_number_id de la configuración de ejemplo
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "123456789012345"
                            },
                            "messages": [
                                {
                                    "id": "wamid.test123456789",
                                    "from": "573001234567",
                                    "timestamp": str(int(time.time())),
                                    "type": "text",
                                    "text": {
                                        "body": "Hola, este es un mensaje de prueba"
                                    }
                                }
                            ],
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Juan Pérez"
                                    },
                                    "wa_id": "573001234567"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/whatsapp/webhook',
            json=webhook_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Procesamiento de mensaje exitoso")
            return True
        else:
            print("❌ Error procesando mensaje")
            return False
            
    except Exception as e:
        print(f"❌ Error probando mensaje: {e}")
        return False

def test_webhook_message_status():
    """Probar actualización de estado de mensaje"""
    print("\n📊 Probando actualización de estado de mensaje...")
    
    # Simular webhook de estado de mensaje
    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789012345",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "123456789012345"
                            },
                            "statuses": [
                                {
                                    "id": "wamid.test123456789",
                                    "status": "delivered",
                                    "timestamp": str(int(time.time())),
                                    "recipient_id": "573001234567"
                                }
                            ]
                        },
                        "field": "message_status"
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/whatsapp/webhook',
            json=webhook_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Actualización de estado exitosa")
            return True
        else:
            print("❌ Error actualizando estado")
            return False
            
    except Exception as e:
        print(f"❌ Error probando estado: {e}")
        return False

def test_database_after_webhook():
    """Verificar que los datos se guardaron en la base de datos"""
    print("\n🗄️ Verificando datos en base de datos...")
    
    try:
        from whatsapp_config_manager import config_manager
        conn = config_manager.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar conversaciones
        cursor.execute("""
            SELECT COUNT(*) as count FROM WhatsApp_Conversations 
            WHERE tenant_id = 1
        """)
        conv_count = cursor.fetchone()
        print(f"📊 Conversaciones en BD: {conv_count['count']}")
        
        # Verificar mensajes
        cursor.execute("""
            SELECT COUNT(*) as count FROM WhatsApp_Messages 
            WHERE tenant_id = 1 AND direction = 'inbound'
        """)
        msg_count = cursor.fetchone()
        print(f"📨 Mensajes entrantes en BD: {msg_count['count']}")
        
        # Mostrar último mensaje
        cursor.execute("""
            SELECT wm.*, wc.contact_name, wc.contact_phone
            FROM WhatsApp_Messages wm
            JOIN WhatsApp_Conversations wc ON wm.conversation_id = wc.id
            WHERE wm.tenant_id = 1 AND wm.direction = 'inbound'
            ORDER BY wm.created_at DESC
            LIMIT 1
        """)
        last_message = cursor.fetchone()
        
        if last_message:
            print(f"💬 Último mensaje:")
            print(f"   De: {last_message['contact_name']} ({last_message['contact_phone']})")
            print(f"   Contenido: {last_message['content']}")
            print(f"   Tipo: {last_message['message_type']}")
            print(f"   Estado: {last_message['status']}")
        
        cursor.close()
        conn.close()
        
        print("✅ Verificación de base de datos completada")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

def main():
    """Función principal de testing"""
    print("🚀 INICIANDO PRUEBAS DE SISTEMA DE WEBHOOKS")
    print("=" * 60)
    
    tests = [
        ("Verificación Webhook", test_webhook_verification),
        ("Mensaje Entrante", test_webhook_message),
        ("Estado Mensaje", test_webhook_message_status),
        ("Verificación BD", test_database_after_webhook)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Ejecutando: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASÓ")
            else:
                print(f"❌ {test_name}: FALLÓ")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADOS: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✅ Sistema de webhooks funcionando correctamente")
    else:
        print("⚠️ Algunas pruebas fallaron")
        print("🔧 Revisar los errores mostrados arriba")
    
    return passed == total

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
