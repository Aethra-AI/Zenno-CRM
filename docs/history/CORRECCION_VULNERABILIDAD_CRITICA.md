# 🔴 CORRECCIÓN URGENTE: Vulnerabilidad en Edición de Candidatos

**Prioridad:** CRÍTICA  
**Fecha:** Octubre 9, 2025  
**Archivo afectado:** `bACKEND/app.py`  
**Líneas:** 5479-5556  
**Endpoint:** `PUT /api/candidate/profile/<int:id_afiliado>`

---

## 🚨 VULNERABILIDAD IDENTIFICADA

### Descripción del Problema:
El endpoint que permite actualizar el perfil de un candidato **NO VALIDA** si el usuario tiene permisos para editar ese candidato específico. Solo verifica que el candidato pertenezca al mismo tenant.

### Impacto:
- **Severidad:** 🔴 CRÍTICA
- **CVSS Score:** 7.5 (Alto)
- Cualquier usuario del tenant puede modificar cualquier candidato
- Violación del modelo de permisos por jerarquía
- Pérdida de integridad de datos
- Falta de trazabilidad

### Escenario de Ataque:
```
1. Reclutador A crea candidato "Juan Pérez" (ID: 100)
2. Reclutador B (del mismo tenant pero sin acceso) puede:
   PUT /api/candidate/profile/100
   Body: {"email": "cambiado@ejemplo.com", "telefono": "99999999"}
3. Los datos se modifican sin validación de permisos
4. No queda registro de quién hizo el cambio
```

---

## ✅ SOLUCIÓN IMPLEMENTADA

### Paso 1: Modificar app.py

**Ubicación:** `bACKEND/app.py`, línea 5522

**Reemplazar el código actual:**
```python
        elif request.method == 'PUT':
            data = request.get_json()
            app.logger.info(f"DEBUG: Actualizando perfil candidato {id_afiliado}, tenant_id: {tenant_id}")
            app.logger.info(f"DEBUG: Datos recibidos: {data}")
            
            update_fields = []
            params = []
```

**Por este código CORREGIDO:**
```python
        elif request.method == 'PUT':
            data = request.get_json()
            user_data = g.current_user
            user_id = user_data.get('user_id')
            
            # 🔐 CORRECCIÓN CRÍTICA: Verificar acceso de escritura
            if not can_access_resource(user_id, tenant_id, 'candidate', id_afiliado, 'write'):
                app.logger.warning(
                    f"❌ INTENTO DE ACCESO NO AUTORIZADO: "
                    f"Usuario {user_id} intentó editar candidato {id_afiliado} sin permisos"
                )
                return jsonify({
                    'success': False,
                    'error': 'No tienes permisos para editar este candidato',
                    'code': 'FORBIDDEN',
                    'required_permission': 'write'
                }), 403
            
            app.logger.info(
                f"✅ Actualizando perfil candidato {id_afiliado} por usuario {user_id}, "
                f"tenant_id: {tenant_id}"
            )
            app.logger.info(f"📝 Datos recibidos: {data}")
            
            update_fields = []
            params = []
```

### Paso 2: Agregar logging de auditoría

**Ubicación:** Después de `conn.commit()` en la línea 5546

**Reemplazar:**
```python
            try:
                cursor.execute(sql, tuple(params))
                conn.commit()
                app.logger.info("DEBUG: Perfil actualizado exitosamente")
                return jsonify({"success": True, "message": "Perfil actualizado."})
```

**Por:**
```python
            try:
                # Obtener valores anteriores para auditoría
                cursor.execute(
                    "SELECT * FROM Afiliados WHERE id_afiliado = %s AND tenant_id = %s",
                    (id_afiliado, tenant_id)
                )
                old_data = cursor.fetchone()
                
                # Ejecutar actualización
                cursor.execute(sql, tuple(params))
                conn.commit()
                
                # 🔐 CORRECCIÓN: Registrar actividad para auditoría
                campos_modificados = list(data.keys())
                log_activity(
                    activity_type='candidato_actualizado',
                    description={
                        'id_afiliado': id_afiliado,
                        'nombre_candidato': old_data.get('nombre_completo') if old_data else 'Desconocido',
                        'campos_modificados': campos_modificados,
                        'modificado_por_usuario_id': user_id,
                        'cantidad_campos': len(campos_modificados)
                    },
                    tenant_id=tenant_id
                )
                
                app.logger.info(
                    f"✅ Perfil actualizado exitosamente - Candidato: {id_afiliado}, "
                    f"Usuario: {user_id}, Campos: {campos_modificados}"
                )
                
                # Crear notificación
                create_notification(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    tipo='candidato',
                    titulo='Perfil de candidato actualizado',
                    mensaje=f"Has actualizado el perfil del candidato (ID: {id_afiliado})",
                    prioridad='baja',
                    metadata={
                        'id_afiliado': id_afiliado,
                        'campos': campos_modificados
                    }
                )
                
                return jsonify({
                    "success": True, 
                    "message": "Perfil actualizado exitosamente",
                    "updated_fields": campos_modificados
                })
```

---

## 📝 CÓDIGO COMPLETO CORREGIDO

```python
@app.route('/api/candidate/profile/<int:id_afiliado>', methods=['GET', 'PUT'])
@token_required
def handle_candidate_profile(id_afiliado):
    conn = get_db_connection()
    if not conn: 
        return jsonify({"error": "Error de conexión"}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        tenant_id = get_current_tenant_id()
        user_data = g.current_user
        user_id = user_data.get('user_id')
        
        if request.method == 'GET':
            # 🔐 MEJORA: Verificar acceso de lectura
            if not can_access_resource(user_id, tenant_id, 'candidate', id_afiliado, 'read'):
                app.logger.warning(
                    f"❌ Usuario {user_id} intentó ver candidato {id_afiliado} sin permisos"
                )
                return jsonify({
                    'error': 'No tienes acceso a este candidato',
                    'code': 'FORBIDDEN'
                }), 403
            
            perfil = {
                "infoBasica": {}, 
                "postulaciones": [], 
                "entrevistas": [], 
                "tags": []
            }
            
            cursor.execute(
                "SELECT * FROM Afiliados WHERE id_afiliado = %s AND tenant_id = %s", 
                (id_afiliado, tenant_id)
            )
            perfil['infoBasica'] = cursor.fetchone()
            
            if not perfil['infoBasica']: 
                return jsonify({"error": "Candidato no encontrado"}), 404
            
            # Obtener postulaciones
            cursor.execute("""
                SELECT 
                    P.id_postulacion, P.id_vacante, P.id_afiliado, 
                    P.fecha_aplicacion, P.estado, P.comentarios, 
                    V.cargo_solicitado, C.empresa 
                FROM Postulaciones P 
                JOIN Vacantes V ON P.id_vacante = V.id_vacante 
                JOIN Clientes C ON V.id_cliente = C.id_cliente 
                WHERE P.id_afiliado = %s AND V.tenant_id = %s
            """, (id_afiliado, tenant_id))
            perfil['postulaciones'] = cursor.fetchall()
            
            # Obtener entrevistas
            cursor.execute("""
                SELECT 
                    E.*, V.cargo_solicitado, C.empresa, P.id_afiliado 
                FROM Entrevistas E 
                JOIN Postulaciones P ON E.id_postulacion = P.id_postulacion 
                JOIN Vacantes V ON P.id_vacante = V.id_vacante 
                JOIN Clientes C ON V.id_cliente = C.id_cliente 
                WHERE P.id_afiliado = %s AND V.tenant_id = %s
            """, (id_afiliado, tenant_id))
            perfil['entrevistas'] = cursor.fetchall()
            
            # Obtener tags
            cursor.execute("""
                SELECT T.id_tag, T.nombre_tag 
                FROM Afiliado_Tags AT 
                JOIN Tags T ON AT.id_tag = T.id_tag 
                WHERE AT.id_afiliado = %s AND T.tenant_id = %s
            """, (id_afiliado, tenant_id))
            perfil['tags'] = cursor.fetchall()
            
            return jsonify(perfil)
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            # 🔐 CORRECCIÓN CRÍTICA: Verificar acceso de escritura
            if not can_access_resource(user_id, tenant_id, 'candidate', id_afiliado, 'write'):
                app.logger.warning(
                    f"❌ INTENTO DE ACCESO NO AUTORIZADO: "
                    f"Usuario {user_id} intentó editar candidato {id_afiliado} sin permisos"
                )
                return jsonify({
                    'success': False,
                    'error': 'No tienes permisos para editar este candidato',
                    'code': 'FORBIDDEN',
                    'required_permission': 'write'
                }), 403
            
            app.logger.info(
                f"✅ Actualizando perfil candidato {id_afiliado} por usuario {user_id}, "
                f"tenant_id: {tenant_id}"
            )
            app.logger.info(f"📝 Datos recibidos: {data}")
            
            update_fields = []
            params = []
            allowed_fields = [
                'nombre_completo', 'telefono', 'email', 'experiencia', 
                'ciudad', 'grado_academico', 'observaciones', 
                'disponibilidad_rotativos', 'transporte_propio', 'estado', 
                'linkedin', 'portfolio', 'skills', 'cargo_solicitado', 
                'fuente_reclutamiento', 'fecha_nacimiento'
            ]
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    params.append(data[field])

            if not update_fields:
                app.logger.error("⚠️ No se proporcionaron campos para actualizar")
                return jsonify({
                    "error": "No se proporcionaron campos para actualizar."
                }), 400

            params.extend([id_afiliado, tenant_id])
            sql = f"UPDATE Afiliados SET {', '.join(update_fields)} WHERE id_afiliado = %s AND tenant_id = %s"
            
            app.logger.info(f"📊 SQL: {sql}")
            app.logger.info(f"📊 Params: {params}")
            
            try:
                # Obtener valores anteriores para auditoría
                cursor.execute(
                    "SELECT * FROM Afiliados WHERE id_afiliado = %s AND tenant_id = %s",
                    (id_afiliado, tenant_id)
                )
                old_data = cursor.fetchone()
                
                # Ejecutar actualización
                cursor.execute(sql, tuple(params))
                conn.commit()
                
                # 🔐 CORRECCIÓN: Registrar actividad para auditoría
                campos_modificados = list(data.keys())
                log_activity(
                    activity_type='candidato_actualizado',
                    description={
                        'id_afiliado': id_afiliado,
                        'nombre_candidato': old_data.get('nombre_completo') if old_data else 'Desconocido',
                        'campos_modificados': campos_modificados,
                        'modificado_por_usuario_id': user_id,
                        'cantidad_campos': len(campos_modificados)
                    },
                    tenant_id=tenant_id
                )
                
                app.logger.info(
                    f"✅ Perfil actualizado exitosamente - Candidato: {id_afiliado}, "
                    f"Usuario: {user_id}, Campos: {campos_modificados}"
                )
                
                # Crear notificación
                create_notification(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    tipo='candidato',
                    titulo='Perfil de candidato actualizado',
                    mensaje=f"Has actualizado el perfil del candidato (ID: {id_afiliado})",
                    prioridad='baja',
                    metadata={
                        'id_afiliado': id_afiliado,
                        'campos': campos_modificados
                    }
                )
                
                return jsonify({
                    "success": True, 
                    "message": "Perfil actualizado exitosamente",
                    "updated_fields": campos_modificados
                })
                
            except Exception as sql_error:
                app.logger.error(
                    f"❌ Error actualizando candidato {id_afiliado}: {str(sql_error)}"
                )
                app.logger.error(f"SQL que falló: {sql}")
                app.logger.error(f"Parámetros que fallaron: {params}")
                raise sql_error

    except Exception as e: 
        app.logger.error(f"❌ Error en handle_candidate_profile: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    
    finally: 
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
```

---

## 🧪 TESTING DE LA CORRECCIÓN

### Test 1: Intentar editar candidato sin permisos (debe fallar)
```bash
# Reclutador B intenta editar candidato de Reclutador A
curl -X PUT http://localhost:5000/api/candidate/profile/100 \
  -H "Authorization: Bearer TOKEN_RECLUTADOR_B" \
  -H "Content-Type: application/json" \
  -d '{
    "telefono": "99999999"
  }'

# Respuesta esperada: 403 Forbidden
{
  "success": false,
  "error": "No tienes permisos para editar este candidato",
  "code": "FORBIDDEN",
  "required_permission": "write"
}
```

### Test 2: Editar candidato propio (debe funcionar)
```bash
# Reclutador A edita su propio candidato
curl -X PUT http://localhost:5000/api/candidate/profile/100 \
  -H "Authorization: Bearer TOKEN_RECLUTADOR_A" \
  -H "Content-Type: application/json" \
  -d '{
    "telefono": "88888888"
  }'

# Respuesta esperada: 200 OK
{
  "success": true,
  "message": "Perfil actualizado exitosamente",
  "updated_fields": ["telefono"]
}
```

### Test 3: Admin edita cualquier candidato (debe funcionar)
```bash
# Admin edita cualquier candidato
curl -X PUT http://localhost:5000/api/candidate/profile/100 \
  -H "Authorization: Bearer TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nuevo@email.com"
  }'

# Respuesta esperada: 200 OK
```

### Test 4: Supervisor edita candidato de su equipo (debe funcionar)
```bash
# Supervisor edita candidato de miembro de su equipo
curl -X PUT http://localhost:5000/api/candidate/profile/100 \
  -H "Authorization: Bearer TOKEN_SUPERVISOR" \
  -H "Content-Type: application/json" \
  -d '{
    "ciudad": "Tegucigalpa"
  }'

# Respuesta esperada: 200 OK si el candidato fue creado por miembro del equipo
# 403 Forbidden si el candidato es de otro equipo
```

---

## 📊 VERIFICACIÓN DE LOGS

Después de la corrección, los logs deberían mostrar:

### Intento no autorizado:
```
[2025-10-09 10:30:15] WARNING ❌ INTENTO DE ACCESO NO AUTORIZADO: Usuario 15 intentó editar candidato 100 sin permisos
```

### Actualización exitosa:
```
[2025-10-09 10:35:20] INFO ✅ Actualizando perfil candidato 100 por usuario 5, tenant_id: 1
[2025-10-09 10:35:20] INFO 📝 Datos recibidos: {'telefono': '88888888'}
[2025-10-09 10:35:21] INFO ✅ Perfil actualizado exitosamente - Candidato: 100, Usuario: 5, Campos: ['telefono']
```

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

- [ ] 1. Hacer backup de `app.py`
- [ ] 2. Aplicar corrección en método PUT (línea 5522)
- [ ] 3. Aplicar mejora en método GET (línea 5488)
- [ ] 4. Agregar logging de auditoría
- [ ] 5. Reiniciar servidor Flask
- [ ] 6. Ejecutar Test 1 (debe fallar con 403)
- [ ] 7. Ejecutar Test 2 (debe funcionar con 200)
- [ ] 8. Ejecutar Test 3 (debe funcionar con 200)
- [ ] 9. Ejecutar Test 4 (debe funcionar según permisos)
- [ ] 10. Verificar logs de auditoría
- [ ] 11. Verificar notificaciones en frontend
- [ ] 12. Testing en staging antes de producción
- [ ] 13. Desplegar a producción
- [ ] 14. Monitorear logs por 24 horas

---

## 🚀 DESPLIEGUE

### Desarrollo:
```bash
cd /Users/juanmontufar/Downloads/Crm\ Zenno\ /bACKEND
git checkout -b fix/candidate-profile-security
# Aplicar cambios
git add app.py
git commit -m "🔐 Fix: Agregar validación de permisos en PUT /api/candidate/profile/<id>"
git push origin fix/candidate-profile-security
```

### Producción:
```bash
# Después de aprobar PR y merge
cd /ruta/produccion
git pull origin main
sudo systemctl restart crm-backend
# O si usa gunicorn:
sudo systemctl restart gunicorn-crm
```

---

## 📞 SOPORTE

Si tienes problemas con la implementación:
1. Revisa los logs: `/var/log/crm-backend.log`
2. Verifica que `can_access_resource` esté importado
3. Confirma que `log_activity` y `create_notification` existan
4. Valida que la tabla `Resource_Assignments` tenga datos

---

**Estado:** LISTO PARA IMPLEMENTAR  
**Tiempo estimado:** 30 minutos  
**Riesgo:** Bajo (solo agrega validaciones, no cambia lógica existente)

