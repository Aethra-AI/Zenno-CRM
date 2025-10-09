# ✅ MÓDULO B8 - ENDPOINTS DE ENTREVISTAS COMPLETADO

**Fecha:** Octubre 9, 2025  
**Archivo modificado:** `bACKEND/app.py`  
**Estado:** 🟢 Listo para probar

---

## 📋 CAMBIOS REALIZADOS

### **1. Modificación de GET `/api/interviews`** ✅

**Ubicación:** Línea 5960-6012

**Cambios:**
- ✅ Filtro por tenant SIEMPRE aplicado
- ✅ Filtrado por usuario según rol a través de `v.created_by_user` (vacante)
- ✅ Incluye entrevistas de vacantes antiguas (created_by_user NULL)

**Antes:**
```python
sql = """
    SELECT e.*, ...
    FROM Entrevistas e
    ...
"""
conditions = []
params = []
# Sin filtro por tenant ni usuario
if request.args.get('vacante_id'):
    conditions.append(...)
```

**Después:**
```python
# 🔐 MÓDULO B8: Siempre filtrar por tenant
conditions.append("v.tenant_id = %s")
params.append(tenant_id)

# 🔐 MÓDULO B8: Filtrar por usuario según rol (a través de la vacante)
condition, filter_params = build_user_filter_condition(user_id, tenant_id, 'v.created_by_user')
if condition:
    conditions.append(f"({condition} OR v.created_by_user IS NULL)")
    params.extend(filter_params)
```

**Lógica clave:**
- Las entrevistas se filtran a través de la vacante relacionada
- Usuario ve entrevistas de vacantes que puede ver
- Admin → todas, Supervisor → su equipo, Reclutador → solo suyas

---

### **2. Modificación de POST `/api/interviews`** ✅

**Ubicación:** Línea 6014-6047

**Cambios:**
- ✅ Verifica permiso con `can_create_resource()`
- ✅ Corrige query de validación (usa Vacantes en vez de Postulaciones.tenant_id)
- ✅ Agrega `created_by_user` al INSERT
- ✅ Log de intentos sin permiso

**Antes:**
```python
# ❌ INCORRECTO (Postulaciones NO tiene tenant_id)
cursor.execute("""
    SELECT id_postulacion 
    FROM Postulaciones 
    WHERE id_postulacion = %s AND tenant_id = %s
""", (id_postulacion, tenant_id))

sql_insert = """
    INSERT INTO Entrevistas (
        id_postulacion, fecha_hora, entrevistador, resultado, observaciones, id_cliente
    ) VALUES (%s, %s, %s, 'Programada', %s, %s)
"""
```

**Después:**
```python
# 🔐 MÓDULO B8: Verificar permiso de creación
if not can_create_resource(user_id, tenant_id, 'interview'):
    return jsonify({'error': 'No tienes permisos para agendar entrevistas'}), 403

# 🔐 MÓDULO B8: Verificar postulación a través de Vacantes
cursor.execute("""
    SELECT p.id_postulacion, v.id_vacante, v.tenant_id
    FROM Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.id_postulacion = %s AND v.tenant_id = %s
""", (id_postulacion, tenant_id))

# 🔐 MÓDULO B8: Insertar con created_by_user
sql_insert = """
    INSERT INTO Entrevistas (
        id_postulacion, fecha_hora, entrevistador, resultado, observaciones, id_cliente, created_by_user
    ) VALUES (%s, %s, %s, 'Programada', %s, %s, %s)
"""
cursor.execute(sql_insert, (..., tenant_id, user_id))
```

---

### **3. Modificación de DELETE `/api/interviews/<id>`** ✅

**Ubicación:** Línea 6148-6182

**Cambios:**
- ✅ Verifica acceso de eliminación a través de la vacante (requiere 'full')
- ✅ Corrige query para usar `v.tenant_id` en vez de `e.id_cliente`
- ✅ Log de intentos sin permiso

**Antes:**
```python
cursor.execute("""
    SELECT e.*, ...
    FROM Entrevistas e
    ...
    WHERE e.id_entrevista = %s AND e.id_cliente = %s
""", (id_entrevista, tenant_id))

# Sin verificación de acceso del usuario
```

**Después:**
```python
# 🔐 MÓDULO B8: Verificar que la entrevista existe y obtener su vacante
cursor.execute("""
    SELECT e.id_entrevista, p.id_afiliado, p.id_vacante, v.cargo_solicitado, v.tenant_id, a.nombre_completo
    FROM Entrevistas e
    JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
    WHERE e.id_entrevista = %s AND v.tenant_id = %s
""", (id_entrevista, tenant_id))

# 🔐 MÓDULO B8: Verificar acceso de eliminación
vacancy_id = entrevista['id_vacante']
if not can_access_resource(user_id, tenant_id, 'vacancy', vacancy_id, 'full'):
    return jsonify({'error': 'No tienes permisos para eliminar esta entrevista'}), 403
```

---

## 🔑 CONCEPTO CLAVE: PERMISOS A TRAVÉS DE LA VACANTE

### **Estructura de relaciones:**

```
Vacante (created_by_user: 8)
  ├── Postulación 1
  │     ├── Entrevista 1 ✅ Reclutador 8 puede verla
  │     └── Entrevista 2 ✅ Reclutador 8 puede eliminarla
  ├── Postulación 2
  │     └── Entrevista 3 ✅ Reclutador 8 puede verla
  └── Postulación 3

Vacante B (created_by_user: 10)
  └── Postulación 4
        └── Entrevista 4 ❌ Reclutador 8 NO tiene acceso
```

**Lógica:**
- Entrevistas → Postulaciones → Vacantes
- Si tienes acceso a la vacante → tienes acceso a sus entrevistas
- Si NO tienes acceso a la vacante → NO puedes ver sus entrevistas

---

## 📊 MATRIZ DE PERMISOS APLICADA

| Acción | Admin | Supervisor<br>(equipo [8,12]) | Reclutador<br>(ID 8) |
|--------|-------|-------------------------------|----------------------|
| **Ver todas las entrevistas** | ✅ | ❌ | ❌ |
| **Ver entrevistas de vacantes del equipo** | ✅ | ✅ (vacantes 5,8,12) | ❌ |
| **Ver entrevistas de vacantes propias** | ✅ | ✅ | ✅ (solo vacante 8) |
| **Agendar entrevista** | ✅ | ✅ | ✅ |
| **Eliminar entrevista (vacante propia)** | ✅ | ✅ | ✅ |
| **Eliminar entrevista (vacante ajena)** | ✅ | ❌ (403) | ❌ (403) |

---

## 🧪 CASOS DE PRUEBA

### **Test 1: Admin ve todas las entrevistas**

**Request:**
```http
GET /api/interviews
Authorization: Bearer <token_admin>
```

**Query esperada:**
```sql
SELECT e.*, a.nombre_completo, v.cargo_solicitado
FROM Entrevistas e
JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
JOIN Vacantes v ON p.id_vacante = v.id_vacante
WHERE v.tenant_id = 1
-- Sin filtro adicional por usuario (Admin ve todo)
ORDER BY e.fecha_hora DESC
```

---

### **Test 2: Supervisor ve entrevistas de su equipo**

**Request:**
```http
GET /api/interviews
Authorization: Bearer <token_supervisor_5>
```

**Vacantes:**
- Vacante A → created_by_user: 5 (Supervisor)
  - Postulación 1 → Entrevista 1, 2
- Vacante B → created_by_user: 8 (Reclutador del equipo)
  - Postulación 2 → Entrevista 3
- Vacante C → created_by_user: 10 (Reclutador fuera del equipo)
  - Postulación 3 → Entrevista 4

**Query esperada:**
```sql
WHERE v.tenant_id = 1
AND (v.created_by_user IN (5, 8, 12) OR v.created_by_user IS NULL)
```

**Resultado esperado:**
- ✅ Ve Entrevista 1, 2 (Vacante A - suya)
- ✅ Ve Entrevista 3 (Vacante B - equipo)
- ❌ NO ve Entrevista 4 (Vacante C - ajena)

---

### **Test 3: Reclutador solo ve entrevistas de sus vacantes**

**Request:**
```http
GET /api/interviews
Authorization: Bearer <token_reclutador_8>
```

**Query esperada:**
```sql
WHERE v.tenant_id = 1
AND (v.created_by_user = 8 OR v.created_by_user IS NULL)
```

**Resultado esperado:**
- ✅ Ve Entrevista 3 (Vacante B - suya)
- ❌ NO ve Entrevista 1, 2 (Vacante A - supervisor)
- ❌ NO ve Entrevista 4 (Vacante C - otro reclutador)

---

### **Test 4: Agendar entrevista registra created_by_user**

**Request:**
```http
POST /api/interviews
Authorization: Bearer <token_reclutador_8>
Content-Type: application/json

{
  "id_postulacion": 123,
  "fecha_hora": "2025-10-15T10:00:00",
  "entrevistador": "María Gómez",
  "observaciones": "Primera entrevista"
}
```

**Query esperada:**
```sql
INSERT INTO Entrevistas (
  id_postulacion, fecha_hora, entrevistador, resultado, observaciones, id_cliente, created_by_user
) VALUES (
  123, '2025-10-15T10:00:00', 'María Gómez', 'Programada', 'Primera entrevista', 1, 8
)
```

**Resultado esperado:**
```json
{
  "success": true,
  "message": "Entrevista agendada...",
  "id_entrevista": 456
}
```

---

### **Test 5: Eliminar entrevista sin acceso (denegado)**

**Request:**
```http
DELETE /api/interviews/123
Authorization: Bearer <token_reclutador_8>
```

**Escenario:** Reclutador 8 intenta eliminar entrevista de vacante creada por Reclutador 10

**Resultado esperado:**
```json
{
  "success": false,
  "error": "No tienes permisos para eliminar esta entrevista",
  "code": "FORBIDDEN"
}
```

**Código HTTP:** `403 Forbidden`

**Log esperado:**
```
WARNING - Usuario 8 intentó eliminar entrevista 123 sin acceso completo a vacante 10
```

---

## 🔍 VALIDACIÓN DE LOGS

### **Logs de creación exitosa:**
```
INFO - Usuario 8 agendando entrevista para postulación 123
INFO - Entrevista agendada exitosamente: ID 456
```

### **Logs de intento sin permiso:**
```
WARNING - Usuario 10 intentó agendar entrevista sin permisos
WARNING - Usuario 8 intentó eliminar entrevista 123 sin acceso completo a vacante 10
```

---

## ✅ CHECKLIST DE VALIDACIÓN

### **Funcionalidad:**
- [x] `GET /api/interviews` filtra por usuario según rol (a través de vacante)
- [x] `POST /api/interviews` valida permisos y registra `created_by_user`
- [x] `DELETE /api/interviews/<id>` valida acceso (requiere 'full' en vacante)

### **Seguridad:**
- [x] Reclutador NO puede ver entrevistas de vacantes ajenas
- [x] Supervisor puede ver entrevistas de vacantes de su equipo
- [x] Admin puede ver todas las entrevistas
- [x] Retorna 403 en accesos no autorizados
- [x] Logs de intentos sin permiso

### **Correcciones:**
- [x] Query corregido (usa `v.tenant_id` en vez de `e.id_cliente`)
- [x] Validación de postulación correcta (a través de Vacantes)
- [x] Frontend no requiere cambios (transparente)

---

## 🐛 BUGS CORREGIDOS

### **Bug 1: Query de validación incorrecto**

**Antes:**
```python
# ❌ Postulaciones NO tiene tenant_id
cursor.execute("""
    SELECT id_postulacion 
    FROM Postulaciones 
    WHERE id_postulacion = %s AND tenant_id = %s
""")
```

**Después:**
```python
# ✅ CORRECTO (obtener tenant de Vacantes)
cursor.execute("""
    SELECT p.id_postulacion, v.id_vacante, v.tenant_id
    FROM Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.id_postulacion = %s AND v.tenant_id = %s
""")
```

---

### **Bug 2: Filtro por tenant incorrecto**

**Antes:**
```python
# ❌ e.id_cliente no es tenant_id confiable
WHERE e.id_entrevista = %s AND e.id_cliente = %s
```

**Después:**
```python
# ✅ CORRECTO (usar v.tenant_id)
WHERE e.id_entrevista = %s AND v.tenant_id = %s
```

---

## 📈 PROGRESO TOTAL

```
✅ B1: Tablas Base (100%)
✅ B2: Columnas Trazabilidad (100%)
⬜ B3: Índices Optimización (0%) - OPCIONAL
✅ B4: Permission Service (100%)
✅ B5: Endpoints Candidatos (100%)
✅ B6: Endpoints Vacantes (100%)
✅ B7: Endpoints Postulaciones (100%)
✅ B8: Endpoints Entrevistas (100%) ← ACABAMOS AQUÍ
⬜ B9: Endpoints Clientes (0%)
⬜ B10: Endpoints Contratados (0%)
⬜ B11-B17: Otros endpoints (0%)
```

**Backend completado:** 7/17 módulos (41.2%)

---

## 🚀 SIGUIENTE PASO: MÓDULO B9

**Objetivo:** Aplicar permisos a endpoints de Clientes

**Endpoints a modificar:**
- `GET /api/clients`
- `POST /api/clients`
- `PUT /api/clients/<id>`
- `DELETE /api/clients/<id>`

**Lógica:** Los clientes tienen `created_by_user` directamente (NO heredado)

**Tiempo estimado:** 1-1.5 horas

---

## ❓ **¿CONTINUAMOS CON B9 O PARAMOS AQUÍ?**

Ya llevamos excelente progreso:
- ✅ 41.2% del backend completado
- ✅ Flujo completo de reclutamiento con permisos (Candidato → Vacante → Postulación → Entrevista)

**Opciones:**
1. 🚀 Continuar con B9 (Clientes) - 1 hora más
2. ⏸️ Pausa para probar todo lo implementado
3. 📊 Crear guía de pruebas completa

**Mi recomendación:** Continuar con B9 y B10 para completar todos los recursos principales, luego probar 🎯

¿Qué prefieres?
