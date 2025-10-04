"""
Test de Importación de Módulos WhatsApp Business API
==================================================
Verifica que todos los módulos se importan correctamente.
"""

def test_imports():
    """Probar importaciones de módulos"""
    print("🚀 INICIANDO PRUEBAS DE IMPORTACIÓN")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Importar WhatsApp Business API Manager
    total_tests += 1
    try:
        from whatsapp_business_api_manager import (
            WhatsAppBusinessAPIManager, 
            send_whatsapp_message, 
            get_whatsapp_message_status,
            api_manager
        )
        print("✅ WhatsApp Business API Manager importado correctamente")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error importando WhatsApp Business API Manager: {e}")
    
    # Test 2: Importar WhatsApp Config Manager
    total_tests += 1
    try:
        from whatsapp_config_manager import (
            config_manager,
            get_tenant_whatsapp_config,
            create_tenant_whatsapp_config,
            update_tenant_whatsapp_config
        )
        print("✅ WhatsApp Config Manager importado correctamente")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error importando WhatsApp Config Manager: {e}")
    
    # Test 3: Importar WhatsApp Webhook Handler
    total_tests += 1
    try:
        from whatsapp_webhook_handler import (
            handle_whatsapp_webhook_get,
            handle_whatsapp_webhook_post
        )
        print("✅ WhatsApp Webhook Handler importado correctamente")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error importando WhatsApp Webhook Handler: {e}")
    
    # Test 4: Crear instancia del API Manager
    total_tests += 1
    try:
        from whatsapp_business_api_manager import WhatsAppBusinessAPIManager
        manager = WhatsAppBusinessAPIManager()
        print("✅ Instancia de API Manager creada correctamente")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error creando instancia de API Manager: {e}")
    
    # Test 5: Verificar métodos del API Manager
    total_tests += 1
    try:
        from whatsapp_business_api_manager import WhatsAppBusinessAPIManager
        manager = WhatsAppBusinessAPIManager()
        
        # Verificar que los métodos existen
        methods = [
            'get_tenant_config',
            'send_text_message',
            'send_template_message',
            'send_media_message',
            'get_message_status'
        ]
        
        for method in methods:
            if not hasattr(manager, method):
                raise AttributeError(f"Método {method} no encontrado")
        
        print("✅ Todos los métodos del API Manager están disponibles")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error verificando métodos del API Manager: {e}")
    
    # Test 6: Verificar funciones de conveniencia
    total_tests += 1
    try:
        from whatsapp_business_api_manager import send_whatsapp_message, get_whatsapp_message_status
        
        # Verificar que las funciones son callable
        if not callable(send_whatsapp_message):
            raise TypeError("send_whatsapp_message no es callable")
        if not callable(get_whatsapp_message_status):
            raise TypeError("get_whatsapp_message_status no es callable")
        
        print("✅ Funciones de conveniencia disponibles")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error verificando funciones de conveniencia: {e}")
    
    # Test 7: Verificar conexión a base de datos
    total_tests += 1
    try:
        import mysql.connector
        
        db_config = {
            'host': 'localhost',
            'database': 'reclutamiento_db',
            'user': 'root',
            'password': 'admin123'
        }
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        print("✅ Conexión a base de datos exitosa")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error conectando a base de datos: {e}")
    
    # Test 8: Verificar tablas de WhatsApp
    total_tests += 1
    try:
        import mysql.connector
        
        db_config = {
            'host': 'localhost',
            'database': 'reclutamiento_db',
            'user': 'root',
            'password': 'admin123'
        }
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Verificar que las tablas existen
        tables = [
            'WhatsApp_Config',
            'WhatsApp_Conversations',
            'WhatsApp_Messages',
            'WhatsApp_Templates'
        ]
        
        for table in tables:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if not cursor.fetchone():
                raise Exception(f"Tabla {table} no existe")
        
        cursor.close()
        conn.close()
        
        print("✅ Todas las tablas de WhatsApp existen")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error verificando tablas: {e}")
    
    # Resultados
    print("\n" + "=" * 50)
    print(f"📊 RESULTADOS: {tests_passed}/{total_tests} pruebas pasaron")
    
    if tests_passed == total_tests:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✅ Sistema de WhatsApp Business API listo para usar")
        return True
    else:
        print("⚠️ Algunas pruebas fallaron - Revisar configuración")
        return False

if __name__ == "__main__":
    test_imports()
