#!/usr/bin/env python3
"""
📱 TEST WHATSAPP IMPLEMENTATION
===============================

Script para probar la implementación de WhatsApp multi-tenant
sin necesidad de que el backend esté ejecutándose.
"""

import sys
import os

def test_imports():
    """Probar que todos los módulos se importan correctamente"""
    print("🔍 Probando importaciones...")
    
    try:
        from whatsapp_config_manager import config_manager
        print("✅ whatsapp_config_manager importado correctamente")
    except Exception as e:
        print(f"❌ Error importando whatsapp_config_manager: {e}")
        return False
    
    try:
        from whatsapp_business_api_manager import WhatsAppBusinessAPIManager
        print("✅ whatsapp_business_api_manager importado correctamente")
    except Exception as e:
        print(f"❌ Error importando whatsapp_business_api_manager: {e}")
        return False
    
    try:
        from whatsapp_webhook_router import WhatsAppWebhookRouter
        print("✅ whatsapp_webhook_router importado correctamente")
    except Exception as e:
        print(f"❌ Error importando whatsapp_webhook_router: {e}")
        return False
    
    return True

def test_database_connection():
    """Probar conexión a base de datos"""
    print("\n🔍 Probando conexión a base de datos...")
    
    try:
        from whatsapp_config_manager import config_manager
        conn = config_manager.get_db_connection()
        
        if conn:
            print("✅ Conexión a base de datos exitosa")
            
            # Probar que las tablas existen
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'WhatsApp_%'")
            tables = cursor.fetchall()
            
            print(f"📊 Tablas WhatsApp encontradas: {len(tables)}")
            for table in tables:
                print(f"   ✅ {table[0]}")
            
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ No se pudo conectar a la base de datos")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando a base de datos: {e}")
        return False

def test_config_manager():
    """Probar funcionalidades del gestor de configuración"""
    print("\n🔍 Probando gestor de configuración...")
    
    try:
        from whatsapp_config_manager import config_manager
        
        # Probar obtención de configuraciones
        configs = config_manager.get_all_tenant_configs()
        print(f"✅ Configuraciones obtenidas: {len(configs)}")
        
        # Probar estadísticas de un tenant
        stats = config_manager.get_tenant_stats(1)
        print(f"✅ Estadísticas obtenidas para tenant 1")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando gestor de configuración: {e}")
        return False

def test_database_tables():
    """Probar estructura de tablas"""
    print("\n🔍 Probando estructura de tablas...")
    
    try:
        from whatsapp_config_manager import config_manager
        conn = config_manager.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar tabla WhatsApp_Config
        cursor.execute("DESCRIBE WhatsApp_Config")
        config_columns = cursor.fetchall()
        print(f"✅ WhatsApp_Config: {len(config_columns)} columnas")
        
        # Verificar tabla WhatsApp_Conversations
        cursor.execute("DESCRIBE WhatsApp_Conversations")
        conv_columns = cursor.fetchall()
        print(f"✅ WhatsApp_Conversations: {len(conv_columns)} columnas")
        
        # Verificar tabla WhatsApp_Messages
        cursor.execute("DESCRIBE WhatsApp_Messages")
        msg_columns = cursor.fetchall()
        print(f"✅ WhatsApp_Messages: {len(msg_columns)} columnas")
        
        # Verificar tabla WhatsApp_Templates
        cursor.execute("DESCRIBE WhatsApp_Templates")
        template_columns = cursor.fetchall()
        print(f"✅ WhatsApp_Templates: {len(template_columns)} columnas")
        
        # Verificar datos iniciales
        cursor.execute("SELECT COUNT(*) as count FROM WhatsApp_Templates WHERE tenant_id = 1")
        template_count = cursor.fetchone()
        print(f"✅ Plantillas iniciales: {template_count['count']}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error probando estructura de tablas: {e}")
        return False

def test_create_sample_config():
    """Probar creación de configuración de ejemplo"""
    print("\n🔍 Probando creación de configuración de ejemplo...")
    
    try:
        from whatsapp_config_manager import config_manager
        
        # Datos de configuración de ejemplo
        config_data = {
            'api_type': 'business_api',
            'business_api_token': 'EAAxxxx_example_token',
            'phone_number_id': '123456789012345',
            'business_account_id': '987654321098765',
            'webhook_verify_token': 'mi_token_secreto_ejemplo'
        }
        
        # Intentar crear configuración
        success, message = config_manager.create_tenant_config(1, config_data)
        
        if success:
            print(f"✅ Configuración creada exitosamente: {message}")
            
            # Obtener la configuración creada
            config = config_manager.get_tenant_config(1, 'business_api')
            if config:
                print(f"✅ Configuración obtenida: {config['api_type']}")
            
            return True
        else:
            print(f"⚠️ No se pudo crear configuración: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando creación de configuración: {e}")
        return False

def main():
    """Función principal de testing"""
    print("🚀 INICIANDO PRUEBAS DE WHATSAPP MULTI-TENANT")
    print("=" * 60)
    
    tests = [
        ("Importaciones", test_imports),
        ("Conexión BD", test_database_connection),
        ("Gestor Config", test_config_manager),
        ("Estructura Tablas", test_database_tables),
        ("Config Ejemplo", test_create_sample_config)
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
        print("✅ Sistema WhatsApp multi-tenant funcionando correctamente")
    else:
        print("⚠️ Algunas pruebas fallaron")
        print("🔧 Revisar los errores mostrados arriba")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
