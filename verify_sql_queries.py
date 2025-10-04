#!/usr/bin/env python3
"""
Script para verificar que todas las consultas SQL en app.py usen tenant_id correctamente
"""

import re
import os

def analyze_sql_queries():
    """Analizar todas las consultas SQL en app.py"""
    
    print("🔍 ANÁLISIS DE CONSULTAS SQL EN APP.PY")
    print("=" * 50)
    
    try:
        with open('app.py', 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"❌ Error leyendo app.py: {e}")
        return False
    
    # Buscar todas las consultas SQL
    sql_patterns = [
        r'cursor\.execute\(["\']([^"\']+)["\']',
        r'cursor\.execute\(f["\']([^"\']+)["\']',
    ]
    
    queries = []
    for pattern in sql_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        queries.extend(matches)
    
    print(f"📊 Se encontraron {len(queries)} consultas SQL")
    print()
    
    # Categorizar consultas
    tenant_queries = []
    client_queries = []
    problematic_queries = []
    
    for query in queries:
        query_lower = query.lower()
        
        # Consultas que deberían usar tenant_id para aislamiento
        if any(table in query_lower for table in [
            'afiliados', 'vacantes', 'postulaciones', 'tags', 
            'email_templates', 'whatsapp_templates', 'contratados'
        ]):
            if 'tenant_id' in query_lower:
                tenant_queries.append(query)
            elif 'id_cliente' in query_lower and 'vacantes' not in query_lower:
                # id_cliente solo debe usarse en Vacantes para vincular con clientes
                problematic_queries.append(query)
            elif 'where' in query_lower and 'tenant_id' not in query_lower:
                # Consultas con WHERE que no usan tenant_id (posible problema)
                if 'users' not in query_lower:  # Users puede tener consultas sin tenant_id
                    problematic_queries.append(query)
        
        # Consultas que correctamente usan id_cliente en Vacantes
        elif 'vacantes' in query_lower and 'id_cliente' in query_lower:
            client_queries.append(query)
    
    # Mostrar resultados
    print("✅ CONSULTAS CORRECTAS CON TENANT_ID:")
    print("-" * 40)
    for i, query in enumerate(tenant_queries[:5], 1):  # Mostrar solo las primeras 5
        print(f"{i}. {query[:80]}...")
    if len(tenant_queries) > 5:
        print(f"... y {len(tenant_queries) - 5} más")
    
    print(f"\n📊 Total consultas con tenant_id: {len(tenant_queries)}")
    
    print("\n✅ CONSULTAS CORRECTAS CON ID_CLIENTE (Vacantes):")
    print("-" * 40)
    for i, query in enumerate(client_queries[:3], 1):
        print(f"{i}. {query[:80]}...")
    if len(client_queries) > 3:
        print(f"... y {len(client_queries) - 3} más")
    
    print(f"\n📊 Total consultas con id_cliente: {len(client_queries)}")
    
    print("\n❌ CONSULTAS PROBLEMÁTICAS:")
    print("-" * 40)
    if problematic_queries:
        for i, query in enumerate(problematic_queries, 1):
            print(f"{i}. {query[:80]}...")
        
        print(f"\n⚠️ Se encontraron {len(problematic_queries)} consultas problemáticas")
        return False
    else:
        print("✅ No se encontraron consultas problemáticas")
        return True

def check_specific_endpoints():
    """Verificar endpoints específicos para multi-tenancy"""
    
    print("\n🔍 VERIFICACIÓN DE ENDPOINTS ESPECÍFICOS")
    print("=" * 50)
    
    try:
        with open('app.py', 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"❌ Error leyendo app.py: {e}")
        return False
    
    # Buscar endpoints que usan get_current_tenant_id()
    tenant_endpoints = re.findall(r'@app\.route\(["\']([^"\']+)["\'].*?def\s+(\w+).*?get_current_tenant_id\(\)', 
                                 content, re.DOTALL)
    
    print("✅ ENDPOINTS QUE USAN TENANT_ID:")
    print("-" * 40)
    for endpoint, function in tenant_endpoints:
        print(f"• {endpoint} -> {function}()")
    
    print(f"\n📊 Total endpoints con tenant_id: {len(tenant_endpoints)}")
    
    # Buscar endpoints sin tenant_id que podrían necesitarlo
    all_endpoints = re.findall(r'@app\.route\(["\']([^"\']+)["\'].*?def\s+(\w+)', content, re.DOTALL)
    
    endpoints_without_tenant = []
    for endpoint, function in all_endpoints:
        if not any(ep[1] == function for ep in tenant_endpoints):
            # Verificar si el endpoint maneja datos que deberían estar aislados
            if any(keyword in endpoint.lower() for keyword in [
                'candidates', 'vacancies', 'applications', 'tags', 'templates'
            ]):
                endpoints_without_tenant.append((endpoint, function))
    
    if endpoints_without_tenant:
        print("\n⚠️ ENDPOINTS QUE PODRÍAN NECESITAR TENANT_ID:")
        print("-" * 40)
        for endpoint, function in endpoints_without_tenant:
            print(f"• {endpoint} -> {function}()")
        
        return False
    else:
        print("\n✅ Todos los endpoints relevantes usan tenant_id")
        return True

def main():
    """Función principal"""
    print("🧪 ANÁLISIS COMPLETO DE CONSULTAS SQL")
    print("=" * 60)
    
    queries_ok = analyze_sql_queries()
    endpoints_ok = check_specific_endpoints()
    
    print("\n📊 RESULTADO FINAL")
    print("=" * 30)
    
    if queries_ok and endpoints_ok:
        print("✅ Todas las consultas SQL están correctas")
        print("✅ Todos los endpoints usan tenant_id apropiadamente")
        return True
    else:
        print("❌ Se encontraron problemas en las consultas SQL o endpoints")
        if not queries_ok:
            print("   - Hay consultas que no usan tenant_id correctamente")
        if not endpoints_ok:
            print("   - Hay endpoints que podrían necesitar tenant_id")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
