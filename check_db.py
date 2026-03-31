import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'whatsapp_backend'),
    charset='utf8mb4',
    collation='utf8mb4_unicode_ci'
)

cursor = conn.cursor(dictionary=True)

cursor.execute("SELECT id, nombre, email, rol_id FROM Users WHERE nombre LIKE '%gisellet%' OR email LIKE '%gisellet%'")
gisellet = cursor.fetchone()

if gisellet:
    print("User Gisellet:", gisellet)
    user_id = gisellet['id']
    
    cursor.execute("SELECT p.modulo, p.ver, p.crear, p.editar, p.eliminar, p.alcance FROM Permisos_Unificados p WHERE p.user_id = %s", (user_id,))
    permisos = cursor.fetchall()
    print("Permisos Gisellet:", permisos)
else:
    cursor.execute("SELECT u.id, u.nombre, r.nombre as rol FROM Users u JOIN Roles r ON u.rol_id = r.id WHERE r.nombre = 'Reclutador'")
    reclutadores = cursor.fetchall()
    print("Reclutadores:", reclutadores)
    if reclutadores:
        user_id = reclutadores[0]['id']
        cursor.execute("SELECT p.modulo, p.ver, p.crear, p.editar, p.eliminar, p.alcance FROM Permisos_Unificados p WHERE p.user_id = %s", (user_id,))
        permisos = cursor.fetchall()
        print(f"Permisos Reclutador {reclutadores[0]['nombre']}:", permisos)

