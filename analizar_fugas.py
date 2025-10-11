#!/usr/bin/env python3
"""
🔍 ANALIZAR FUGAS DE INFORMACIÓN EN ENDPOINTS
Este script analiza app.py y detecta endpoints que NO usan filtros de permisos
"""

import re

def analizar_endpoints():
    """Analiza app.py para encontrar endpoints sin filtros"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Encontrar todos los endpoints GET
    patron_endpoint = r"@app\.route\('(/api/[^']+)'.*methods=\[.*GET.*\]\)\s*\n@token_required\s*\ndef\s+(\w+)"
    endpoints = re.findall(patron_endpoint, contenido)
    
    print("=" * 60)
    print("🔍 ANÁLISIS DE ENDPOINTS CON POSIBLES FUGAS")
    print("=" * 60)
    
    endpoints_criticos = []
    
    for ruta, nombre_funcion in endpoints:
        # Buscar si el endpoint crítico (candidatos, vacantes, etc.)
        es_critico = any(keyword in ruta.lower() for keyword in [
            'candidate', 'vacanc', 'client', 'application', 
            'interview', 'hired', 'dashboard', 'report', 'kpi', 'activit'
        ])
        
        if not es_critico:
            continue
        
        # Buscar el código de la función
        patron_funcion = rf"def {nombre_funcion}\([^)]*\):.*?(?=\ndef\s+\w+|@app\.route|\Z)"
        match_funcion = re.search(patron_funcion, contenido, re.DOTALL)
        
        if not match_funcion:
            continue
        
        codigo_funcion = match_funcion.group(0)
        
        # Verificar si usa filtros
        usa_build_filter = 'build_user_filter_condition' in codigo_funcion
        usa_accessible_ids = 'get_accessible_user_ids' in codigo_funcion
        usa_is_admin = 'is_admin(' in codigo_funcion
        tiene_tenant_filter = 'tenant_id' in codigo_funcion
        
        tiene_filtro = usa_build_filter or usa_accessible_ids or usa_is_admin
        
        # Determinar severidad
        if 'dashboard' in ruta.lower() or 'report' in ruta.lower() or 'kpi' in ruta.lower():
            severidad = "🔴 CRÍTICA"
        elif 'client' in ruta.lower() or 'hired' in ruta.lower():
            severidad = "🟠 ALTA"
        else:
            severidad = "🟡 MEDIA"
        
        info = {
            'ruta': ruta,
            'funcion': nombre_funcion,
            'tiene_filtro': tiene_filtro,
            'usa_build_filter': usa_build_filter,
            'usa_accessible_ids': usa_accessible_ids,
            'usa_is_admin': usa_is_admin,
            'tiene_tenant_filter': tiene_tenant_filter,
            'severidad': severidad
        }
        
        endpoints_criticos.append(info)
    
    # Mostrar resultados
    print(f"\n📊 Total de endpoints críticos encontrados: {len(endpoints_criticos)}\n")
    
    con_filtro = [e for e in endpoints_criticos if e['tiene_filtro']]
    sin_filtro = [e for e in endpoints_criticos if not e['tiene_filtro']]
    
    print(f"✅ Con filtros de permisos: {len(con_filtro)}")
    print(f"❌ Sin filtros de permisos: {len(sin_filtro)}\n")
    
    if sin_filtro:
        print("=" * 60)
        print("🚨 ENDPOINTS SIN FILTROS (FUGAS DETECTADAS)")
        print("=" * 60)
        
        for endpoint in sin_filtro:
            print(f"\n{endpoint['severidad']} {endpoint['ruta']}")
            print(f"   Función: {endpoint['funcion']}()")
            print(f"   Tiene tenant_id: {'Sí' if endpoint['tiene_tenant_filter'] else 'No'}")
            print(f"   NECESITA: Agregar build_user_filter_condition() o get_accessible_user_ids()")
    
    if con_filtro:
        print("\n" + "=" * 60)
        print("✅ ENDPOINTS CON FILTROS (CORRECTOS)")
        print("=" * 60)
        
        for endpoint in con_filtro:
            print(f"\n✅ {endpoint['ruta']}")
            print(f"   Función: {endpoint['funcion']}()")
            if endpoint['usa_build_filter']:
                print(f"   Usa: build_user_filter_condition()")
            if endpoint['usa_accessible_ids']:
                print(f"   Usa: get_accessible_user_ids()")
            if endpoint['usa_is_admin']:
                print(f"   Usa: is_admin()")
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN")
    print("=" * 60)
    print(f"Total analizado: {len(endpoints_criticos)}")
    print(f"Con filtros: {len(con_filtro)} ✅")
    print(f"Sin filtros: {len(sin_filtro)} ❌")
    
    if sin_filtro:
        print(f"\n⚠️  Se detectaron {len(sin_filtro)} endpoints con posibles fugas")
        print("   Estos endpoints deben corregirse URGENTEMENTE")
    else:
        print("\n✅ Todos los endpoints críticos tienen filtros")
    
    print("\n" + "=" * 60)
    
    return sin_filtro, con_filtro

if __name__ == "__main__":
    sin_filtro, con_filtro = analizar_endpoints()
    
    if sin_filtro:
        print("\n🔧 PRÓXIMO PASO:")
        print("   Ejecutar script de corrección automática para estos endpoints")
    else:
        print("\n🎉 ¡Sistema seguro! Todos los endpoints usan filtros")

