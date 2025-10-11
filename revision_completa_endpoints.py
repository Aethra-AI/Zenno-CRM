#!/usr/bin/env python3
"""
🔍 REVISIÓN COMPLETA DE TODOS LOS ENDPOINTS
Analiza los 111 endpoints y verifica que estén correctamente protegidos
"""

import re

def analizar_endpoint(ruta, metodos, nombre_funcion, codigo_funcion, linea):
    """Analiza un endpoint y determina su nivel de protección"""
    
    # Determinar si necesita protección
    es_publico = any(palabra in ruta.lower() for palabra in [
        'webhook', 'health', 'test', 'ping', 'bot_tools'
    ])
    
    # Verificar decoradores de seguridad
    tiene_token_required = '@token_required' in codigo_funcion
    tiene_admin_required = '@admin_required' in codigo_funcion
    tiene_api_key = '@require_api_key' in codigo_funcion
    
    # Verificar filtros de datos
    usa_tenant_id = 'tenant_id' in codigo_funcion or 'get_current_tenant_id()' in codigo_funcion
    usa_build_filter = 'build_user_filter_condition' in codigo_funcion
    usa_can_access = 'can_access_resource' in codigo_funcion
    usa_accessible_ids = 'get_accessible_user_ids' in codigo_funcion
    usa_is_admin = 'is_admin(' in codigo_funcion
    usa_is_supervisor = 'is_supervisor(' in codigo_funcion
    
    # Determinar tipo de endpoint
    es_listado = 'GET' in metodos and not any(char in ruta for char in ['<int:', '<string:'])
    es_individual = 'GET' in metodos and any(char in ruta for char in ['<int:', '<string:'])
    es_escritura = any(metodo in metodos for metodo in ['POST', 'PUT', 'DELETE'])
    
    # Determinar criticidad
    palabras_criticas = ['dashboard', 'report', 'kpi', 'metrics', 'stats', 'financial', 'revenue']
    palabras_sensibles = ['client', 'hired', 'payment', 'salary']
    palabras_importantes = ['candidate', 'vacancy', 'application', 'interview', 'user']
    
    if any(palabra in ruta.lower() for palabra in palabras_criticas):
        criticidad = "🔴 CRÍTICA"
    elif any(palabra in ruta.lower() for palabra in palabras_sensibles):
        criticidad = "🟠 ALTA"
    elif any(palabra in ruta.lower() for palabra in palabras_importantes):
        criticidad = "🟡 MEDIA"
    else:
        criticidad = "🟢 BAJA"
    
    # Determinar si tiene protección adecuada
    tiene_autenticacion = tiene_token_required or tiene_admin_required or tiene_api_key
    tiene_filtrado = usa_build_filter or usa_can_access or usa_accessible_ids
    
    # Análisis de seguridad
    if es_publico:
        nivel_seguridad = "✅ PÚBLICO" if tiene_api_key or 'webhook' in ruta else "⚠️ PÚBLICO SIN KEY"
        necesita_correccion = not tiene_api_key and 'webhook' not in ruta
    elif not tiene_autenticacion:
        nivel_seguridad = "❌ SIN AUTENTICACIÓN"
        necesita_correccion = True
    elif es_listado and not tiene_filtrado and not es_publico:
        nivel_seguridad = "⚠️ LISTADO SIN FILTROS"
        necesita_correccion = True
    elif es_individual and not tiene_filtrado and not usa_tenant_id:
        nivel_seguridad = "⚠️ SIN VALIDACIÓN DE ACCESO"
        necesita_correccion = True
    else:
        nivel_seguridad = "✅ PROTEGIDO"
        necesita_correccion = False
    
    return {
        'ruta': ruta,
        'metodos': metodos,
        'funcion': nombre_funcion,
        'linea': linea,
        'criticidad': criticidad,
        'es_publico': es_publico,
        'tiene_autenticacion': tiene_autenticacion,
        'tiene_token_required': tiene_token_required,
        'tiene_admin_required': tiene_admin_required,
        'tiene_api_key': tiene_api_key,
        'usa_tenant_id': usa_tenant_id,
        'usa_build_filter': usa_build_filter,
        'usa_can_access': usa_can_access,
        'usa_accessible_ids': usa_accessible_ids,
        'usa_is_admin': usa_is_admin,
        'tiene_filtrado': tiene_filtrado,
        'es_listado': es_listado,
        'es_individual': es_individual,
        'nivel_seguridad': nivel_seguridad,
        'necesita_correccion': necesita_correccion
    }

def main():
    """Ejecutar análisis completo"""
    print("=" * 80)
    print("🔍 REVISIÓN COMPLETA DE SEGURIDAD - 111 ENDPOINTS")
    print("=" * 80)
    
    with open('app.py', 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Encontrar todos los endpoints
    patron = r"@app\.route\('([^']+)',?\s*methods=\[([^\]]+)\]\)\s*(?:@\w+\s*)*\ndef\s+(\w+)"
    matches = list(re.finditer(patron, contenido))
    
    print(f"\n📊 Total de endpoints encontrados: {len(matches)}\n")
    
    # Analizar cada endpoint
    todos_endpoints = []
    
    for match in matches:
        ruta = match.group(1)
        metodos = match.group(2).replace("'", "").replace('"', '').split(',')
        metodos = [m.strip() for m in metodos]
        nombre_funcion = match.group(3)
        linea = contenido[:match.start()].count('\n') + 1
        
        # Obtener código de la función (hasta la siguiente función o decorador)
        start = match.start()
        # Buscar el siguiente @app.route o final del archivo
        next_route = re.search(r'\n@app\.route', contenido[match.end():])
        if next_route:
            end = match.end() + next_route.start()
        else:
            end = len(contenido)
        
        codigo_funcion = contenido[start:end]
        
        # Analizar
        analisis = analizar_endpoint(ruta, metodos, nombre_funcion, codigo_funcion, linea)
        todos_endpoints.append(analisis)
    
    # Agrupar por nivel de seguridad
    protegidos = [e for e in todos_endpoints if e['nivel_seguridad'] == '✅ PROTEGIDO']
    publicos_ok = [e for e in todos_endpoints if e['nivel_seguridad'] == '✅ PÚBLICO']
    necesitan_correccion = [e for e in todos_endpoints if e['necesita_correccion']]
    
    # Agrupar por criticidad
    criticos = [e for e in necesitan_correccion if '🔴' in e['criticidad']]
    altos = [e for e in necesitan_correccion if '🟠' in e['criticidad']]
    medios = [e for e in necesitan_correccion if '🟡' in e['criticidad']]
    bajos = [e for e in necesitan_correccion if '🟢' in e['criticidad']]
    
    # RESUMEN GENERAL
    print("=" * 80)
    print("📊 RESUMEN GENERAL")
    print("=" * 80)
    print(f"Total de endpoints: {len(todos_endpoints)}")
    print(f"✅ Correctamente protegidos: {len(protegidos)}")
    print(f"✅ Públicos (con API key): {len(publicos_ok)}")
    print(f"⚠️  Necesitan corrección: {len(necesitan_correccion)}")
    print()
    
    if necesitan_correccion:
        print(f"Por criticidad:")
        print(f"  🔴 CRÍTICA: {len(criticos)}")
        print(f"  🟠 ALTA: {len(altos)}")
        print(f"  🟡 MEDIA: {len(medios)}")
        print(f"  🟢 BAJA: {len(bajos)}")
    
    # ENDPOINTS QUE NECESITAN CORRECCIÓN
    if necesitan_correccion:
        print("\n" + "=" * 80)
        print("⚠️  ENDPOINTS QUE NECESITAN CORRECCIÓN")
        print("=" * 80)
        
        for categoria, lista in [
            ("🔴 CRÍTICOS", criticos),
            ("🟠 ALTA PRIORIDAD", altos),
            ("🟡 MEDIA PRIORIDAD", medios),
            ("🟢 BAJA PRIORIDAD", bajos)
        ]:
            if lista:
                print(f"\n{categoria}: ({len(lista)})")
                for e in lista:
                    print(f"\n  {e['nivel_seguridad']} Línea {e['linea']}: {e['ruta']}")
                    print(f"     Función: {e['funcion']}()")
                    print(f"     Métodos: {', '.join(e['metodos'])}")
                    
                    problemas = []
                    if not e['tiene_autenticacion']:
                        problemas.append("Sin autenticación (@token_required)")
                    if e['es_listado'] and not e['tiene_filtrado']:
                        problemas.append("Listado sin filtros por usuario")
                    if not e['usa_tenant_id'] and not e['es_publico']:
                        problemas.append("No valida tenant_id")
                    
                    if problemas:
                        print(f"     Problemas detectados:")
                        for p in problemas:
                            print(f"       - {p}")
    
    # ENDPOINTS CORRECTOS (muestra algunos ejemplos)
    print("\n" + "=" * 80)
    print("✅ ENDPOINTS CORRECTAMENTE PROTEGIDOS (Ejemplos)")
    print("=" * 80)
    
    ejemplos_protegidos = [e for e in protegidos if any(palabra in e['ruta'].lower() 
                          for palabra in ['dashboard', 'candidate', 'vacancy', 'user', 'client'])]
    
    for e in ejemplos_protegidos[:10]:
        print(f"\n  ✅ {e['ruta']}")
        print(f"     Línea: {e['linea']}, Función: {e['funcion']}()")
        
        protecciones = []
        if e['tiene_token_required']:
            protecciones.append("@token_required")
        if e['tiene_admin_required']:
            protecciones.append("@admin_required")
        if e['usa_build_filter']:
            protecciones.append("build_user_filter_condition()")
        if e['usa_can_access']:
            protecciones.append("can_access_resource()")
        if e['usa_accessible_ids']:
            protecciones.append("get_accessible_user_ids()")
        
        if protecciones:
            print(f"     Protecciones: {', '.join(protecciones)}")
    
    if len(protegidos) > 10:
        print(f"\n  ... y {len(protegidos) - 10} endpoints más correctamente protegidos")
    
    # RESUMEN FINAL
    print("\n" + "=" * 80)
    print("🎯 CONCLUSIÓN")
    print("=" * 80)
    
    porcentaje_seguro = (len(protegidos) + len(publicos_ok)) / len(todos_endpoints) * 100
    
    print(f"\nCobertura de seguridad: {porcentaje_seguro:.1f}%")
    print(f"Endpoints seguros: {len(protegidos) + len(publicos_ok)}/{len(todos_endpoints)}")
    
    if necesitan_correccion:
        print(f"\n⚠️  ACCIÓN REQUERIDA: {len(necesitan_correccion)} endpoints necesitan corrección")
        print("   Prioridad:")
        if criticos:
            print(f"   1. CRÍTICOS ({len(criticos)}) - Corregir INMEDIATAMENTE")
        if altos:
            print(f"   2. ALTOS ({len(altos)}) - Corregir HOY")
        if medios:
            print(f"   3. MEDIOS ({len(medios)}) - Corregir esta semana")
    else:
        print("\n✅ ¡PERFECTO! Todos los endpoints están correctamente protegidos")
    
    print("\n" + "=" * 80)
    
    return todos_endpoints, necesitan_correccion

if __name__ == "__main__":
    todos, con_problemas = main()
    
    # Guardar reporte en archivo
    with open('REPORTE_REVISION_COMPLETA.txt', 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("REPORTE COMPLETO DE REVISIÓN DE ENDPOINTS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total de endpoints: {len(todos)}\n")
        f.write(f"Seguros: {len([e for e in todos if not e['necesita_correccion']])}\n")
        f.write(f"Con problemas: {len(con_problemas)}\n\n")
        
        if con_problemas:
            f.write("ENDPOINTS CON PROBLEMAS:\n")
            f.write("-" * 80 + "\n")
            for e in con_problemas:
                f.write(f"\n{e['criticidad']} Línea {e['linea']}: {e['ruta']}\n")
                f.write(f"  Función: {e['funcion']}()\n")
                f.write(f"  Métodos: {', '.join(e['metodos'])}\n")
                f.write(f"  Nivel: {e['nivel_seguridad']}\n")
        
        f.write("\n\nENDPOINTS SEGUROS:\n")
        f.write("-" * 80 + "\n")
        for e in todos:
            if not e['necesita_correccion']:
                f.write(f"✅ {e['ruta']} (línea {e['linea']})\n")
    
    print("\n📄 Reporte guardado en: REPORTE_REVISION_COMPLETA.txt")

