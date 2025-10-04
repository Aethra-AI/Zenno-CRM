#!/usr/bin/env python3
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def check_tables():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'zenno_crm')
        )
        cursor = conn.cursor()
        
        # Verificar calendar_reminders
        cursor.execute("SHOW TABLES LIKE 'calendar_reminders'")
        result = cursor.fetchone()
        print(f"calendar_reminders: {'✅ Existe' if result else '❌ No existe'}")
        
        # Verificar interviews
        cursor.execute("SHOW TABLES LIKE 'interviews'")
        result = cursor.fetchone()
        print(f"interviews: {'✅ Existe' if result else '❌ No existe'}")
        
        # Verificar estructura de calendar_reminders
        if cursor.execute("SHOW TABLES LIKE 'calendar_reminders'"):
            cursor.execute("DESCRIBE calendar_reminders")
            columns = cursor.fetchall()
            print(f"\nEstructura de calendar_reminders:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_tables()
