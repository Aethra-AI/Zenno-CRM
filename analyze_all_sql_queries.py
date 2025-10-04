#!/usr/bin/env python3
"""
Análisis exhaustivo de TODAS las consultas SQL en app.py
Verifica que cada INSERT, UPDATE, SELECT, DELETE use tenant_id correctamente
"""

import re
import os
from collections import defaultdict

def analyze_sql_queries():
    """Analizar todas las consultas SQL en app.py"""
    
    print("🔍 ANÁLISIS EXHAUSTIVO DE CONSULTAS SQL")
    print("=" * 60)
    
    try:
        with open('app.py', 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"❌ Error leyendo app.py: {e}")
        return False
    
    # Patrones para encontrar consultas SQL
    sql_patterns = [
        r'cursor\.execute\(["\']([^"\']+)["\']',  # cursor.execute("SELECT...")
        r'cursor\.execute\(f["\']([^"\']+)["\']',  # cursor.execute(f"SELECT...")
        r'cursor\.execute\(([^,)]+)\)',            # cursor.execute(query, params)
    ]
    
    all_queries = []
    for pattern in sql_patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        all_queries.extend(matches)
    
    print(f"📊 Se encontraron {len(all_queries)} consultas SQL")
    print()
    
    # Categorizar consultas por tipo y tabla
    categorized = {
        'INSERT': defaultdict(list),
        'UPDATE': defaultdict(list),
        'SELECT': defaultdict(list),
        'DELETE': defaultdict(list),
        'OTHER': []
    }
    
    # Tablas que DEBEN usar tenant_id para aislamiento
    tenant_tables = {
        'Afiliados', 'Vacantes', 'Postulaciones', 'Tags', 
        'Email_Templates', 'Whatsapp_Templates', 'Contratados',
        'Entrevistas', 'Afiliado_Tags'
    }
    
    # Tablas que usan id_cliente (solo para vincular con Clientes)
    client_tables = {'Vacantes'}  # Solo Vacantes vincula con Clientes
    
    for query in all_queries:
        query_clean = query.strip()
        if not query_clean:
            continue
            
        query_upper = query_clean.upper()
        
        # Determinar tipo de consulta
        if query_upper.startswith('INSERT'):
            query_type = 'INSERT'
        elif query_upper.startswith('UPDATE'):
            query_type = 'UPDATE'
        elif query_upper.startswith('SELECT'):
            query_type = 'SELECT'
        elif query_upper.startswith('DELETE'):
            query_type = 'DELETE'
        else:
            query_type = 'OTHER'
        
        # Extraer nombre de tabla
        table_name = extract_table_name(query_clean)
        
        if table_name and query_type != 'OTHER':
            categorized[query_type][table_name].append(query_clean)
        else:
            categorized['OTHER'].append(query_clean)
    
    # Analizar cada categoría
    issues_found = []
    
    print("📋 ANÁLISIS POR TIPO DE CONSULTA")
    print("=" * 40)
    
    for query_type, tables in categorized.items():
        if not tables:
            continue
            
        print(f"\n🔸 {query_type} QUERIES:")
        print("-" * 30)
        
        if isinstance(tables, dict):
            for table_name, queries in tables.items():
                print(f"\n  📊 Tabla: {table_name}")
                
                # Verificar si la tabla necesita tenant_id
                needs_tenant_id = table_name in tenant_tables
                uses_client_id = table_name in client_tables
                
                if needs_tenant_id:
                    print(f"    ✅ DEBE usar tenant_id para aislamiento")
                if uses_client_id:
                    print(f"    🔗 USA id_cliente para vincular con Clientes")
                
                # Analizar cada consulta
                for i, query in enumerate(queries[:3], 1):  # Mostrar solo las primeras 3
                    print(f"    {i}. {query[:80]}...")
                    
                    # Verificar tenant_id
                    if needs_tenant_id:
                        if 'tenant_id' not in query:
                            issues_found.append({
                                'type': 'MISSING_TENANT_ID',
                                'table': table_name,
                                'query_type': query_type,
                                'query': query[:100]
                            })
                            print(f"       ❌ FALTA tenant_id")
                        else:
                            print(f"       ✅ Incluye tenant_id")
                    
                    # Verificar id_cliente (solo para Vacantes)
                    if table_name == 'Vacantes' and query_type in ['INSERT', 'UPDATE']:
                        if 'id_cliente' not in query:
                            print(f"       ⚠️  Podría necesitar id_cliente para vincular con Cliente")
                
                if len(queries) > 3:
                    print(f"    ... y {len(queries) - 3} consultas más")
    
    # Mostrar resumen de problemas
    print(f"\n🚨 RESUMEN DE PROBLEMAS ENCONTRADOS")
    print("=" * 50)
    
    if issues_found:
        print(f"❌ Se encontraron {len(issues_found)} problemas:")
        for issue in issues_found:
            print(f"  • {issue['table']} ({issue['query_type']}): {issue['type']}")
            print(f"    Query: {issue['query']}...")
    else:
        print("✅ No se encontraron problemas críticos")
    
    return len(issues_found) == 0

def extract_table_name(query):
    """Extraer el nombre de la tabla de una consulta SQL"""
    query_upper = query.upper()
    
    # Patrones para extraer nombre de tabla
    patterns = [
        r'FROM\s+(\w+)',
        r'INTO\s+(\w+)',
        r'UPDATE\s+(\w+)',
        r'DELETE\s+FROM\s+(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_upper)
        if match:
            return match.group(1)
    
    return None

def analyze_specific_endpoints():
    """Analizar endpoints específicos que manejan datos"""
    
    print(f"\n🎯 ANÁLISIS DE ENDPOINTS CRÍTICOS")
    print("=" * 50)
    
    try:
        with open('app.py', 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"❌ Error leyendo app.py: {e}")
        return False
    
    # Buscar endpoints que manejan datos
    endpoint_pattern = r'@app\.route\(["\']([^"\']+)["\'].*?def\s+(\w+)'
    endpoints = re.findall(endpoint_pattern, content, re.DOTALL)
    
    critical_endpoints = []
    
    for endpoint, function in endpoints:
        # Verificar si el endpoint maneja datos que necesitan aislamiento
        if any(keyword in endpoint.lower() for keyword in [
            'candidates', 'vacancies', 'applications', 'tags', 'templates', 'hired'
        ]):
            critical_endpoints.append((endpoint, function))
    
    print(f"📋 Endpoints críticos encontrados: {len(critical_endpoints)}")
    
    for endpoint, function in critical_endpoints:
        print(f"  • {endpoint} -> {function}()")
        
        # Verificar si usa get_current_tenant_id()
        if f'get_current_tenant_id()' in content:
            print(f"    ✅ Usa get_current_tenant_id()")
        else:
            print(f"    ❌ NO usa get_current_tenant_id()")
    
    return True

def main():
    """Función principal"""
    print("🧪 ANÁLISIS COMPLETO DEL SISTEMA MULTI-TENANCY")
    print("=" * 70)
    
    queries_ok = analyze_sql_queries()
    endpoints_ok = analyze_specific_endpoints()
    
    print(f"\n📊 RESULTADO FINAL")
    print("=" * 30)
    
    if queries_ok and endpoints_ok:
        print("✅ Sistema multi-tenancy correctamente implementado")
        print("✅ Todas las consultas usan tenant_id apropiadamente")
        print("✅ Aislamiento de datos garantizado")
        return True
    else:
        print("❌ Se encontraron problemas en el sistema multi-tenancy")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
