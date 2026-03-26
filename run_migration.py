#!/usr/bin/env python3
"""
Script para ejecutar migración 003 en Supabase
"""
import os
from sqlalchemy import create_engine, text

# Leer DATABASE_URL del .env
DATABASE_URL = "postgresql://postgres.xorxplnzfdnmuiecgvtt:lpCYw8QVXy6DR0dA@aws-0-us-west-2.pooler.supabase.com:6543/postgres"

print("🔥 Ejecutando migración 003_users_teams.sql en Supabase...")

# Leer archivo SQL
with open("migrations/003_users_teams.sql", "r") as f:
    migration_sql = f.read()

# Crear engine
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # Ejecutar migración
        conn.execute(text(migration_sql))
        conn.commit()
        print("✅ Migración ejecutada exitosamente")
        
        # Verificar tablas creadas
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'teams', 'user_agent_assignments')
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result]
        print(f"\n✅ Tablas creadas: {', '.join(tables)}")
        
        # Verificar usuarios seeded
        result = conn.execute(text("SELECT COUNT(*) FROM users;"))
        user_count = result.scalar()
        print(f"✅ Usuarios seeded: {user_count}")
        
        # Verificar equipos seeded
        result = conn.execute(text("SELECT COUNT(*) FROM teams;"))
        team_count = result.scalar()
        print(f"✅ Equipos seeded: {team_count}")
        
except Exception as e:
    print(f"❌ Error ejecutando migración: {e}")
    raise

print("\n🔥 Migración completada. Listo para deploy.")
