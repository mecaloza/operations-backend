#!/usr/bin/env python3
"""
Ejecutar migración 005: Epic Evaluation Points
"""
import psycopg2
import sys

DATABASE_URL = "postgresql://postgres.xorxplnzfdnmuiecgvtt:lpCYw8QVXy6DR0dA@aws-0-us-west-2.pooler.supabase.com:6543/postgres"

def run_migration():
    print("🔥 Ejecutando migración 005: Epic Evaluation Points")
    
    # Leer SQL
    with open("migrations/005_epic_evaluation_points.sql", "r") as f:
        sql = f.read()
    
    # Conectar a DB
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("✅ Conectado a Supabase")
        
        # Ejecutar SQL
        cursor.execute(sql)
        conn.commit()
        
        print("✅ Migración ejecutada exitosamente")
        
        # Verificar tabla creada
        cursor.execute("SELECT COUNT(*) FROM epic_evaluation_points;")
        count = cursor.fetchone()[0]
        print(f"✅ Tabla epic_evaluation_points: {count} registros")
        
        cursor.close()
        conn.close()
        
        print("\n🔥 Migración 005 completada exitosamente")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_migration())
