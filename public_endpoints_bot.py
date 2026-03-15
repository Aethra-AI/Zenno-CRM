
@app.route('/api/public/vacancies', methods=['GET'])
@public_api_key_required
def get_public_vacancies():
    """Endpoint público para que el agente consulte vacantes del tenant"""
    tenant_id = g.tenant_id
    city = request.args.get('city')
    keyword = request.args.get('keyword')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id_vacante, cargo_solicitado, requisitos, ciudad, salario FROM Vacantes WHERE tenant_id = %s AND estado = 'Abierta'"
        params = [tenant_id]
        
        if city:
            query += " AND ciudad LIKE %s"
            params.append(f"%{city}%")
        if keyword:
            query += " AND (cargo_solicitado LIKE %s OR requisitos LIKE %s)"
            params.append(f"%{keyword}%")
            params.append(f"%{keyword}%")
            
        cursor.execute(query, tuple(params))
        return jsonify(cursor.fetchall()), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/api/public/candidates', methods=['GET'])
@public_api_key_required
def get_public_candidates():
    """Endpoint público para buscar candidatos existentes"""
    tenant_id = g.tenant_id
    identity = request.args.get('identity')
    name = request.args.get('name')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id_afiliado, nombre_completo, identidad, telefono FROM Afiliados WHERE tenant_id = %s"
        params = [tenant_id]
        
        if identity:
            query += " AND identidad = %s"
            params.append(identity)
        if name:
            query += " AND nombre_completo LIKE %s"
            params.append(f"%{name}%")
            
        cursor.execute(query, tuple(params))
        return jsonify(cursor.fetchall()), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/api/public/applications', methods=['POST'])
@public_api_key_required
def post_public_application():
    """Endpoint público para registrar una nueva postulación desde el agente"""
    tenant_id = g.tenant_id
    data = request.get_json()
    
    vacancy_id = data.get('vacancy_id')
    candidate = data.get('candidate', {})
    
    if not vacancy_id or not candidate.get('identidad'):
        return jsonify({"error": "vacancy_id e identidad del candidato son requeridos"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Verificar/Crear Afiliado
        cursor.execute("SELECT id_afiliado FROM Afiliados WHERE identidad = %s AND tenant_id = %s", 
                     (candidate['identidad'], tenant_id))
        res = cursor.fetchone()
        
        if res:
            candidate_id = res['id_afiliado']
        else:
            sql_c = "INSERT INTO Afiliados (tenant_id, nombre_completo, identidad, telefono, creado_en) VALUES (%s, %s, %s, %s, NOW())"
            cursor.execute(sql_c, (tenant_id, candidate.get('nombre'), candidate['identidad'], candidate.get('telefono')))
            candidate_id = cursor.lastrowid
            
        # 2. Registrar Postulación
        sql_p = "INSERT INTO Postulaciones (tenant_id, id_afiliado, id_vacante, fecha_aplicacion, estado) VALUES (%s, %s, %s, NOW(), 'Recibida')"
        cursor.execute(sql_p, (tenant_id, candidate_id, vacancy_id))
        conn.commit()
        
        return jsonify({"success": True, "candidate_id": candidate_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
