#!/usr/bin/env python3
"""
RECOVERY SCRIPT - Recrear tablas perdidas
REGLA CRÍTICA: SOLO CREATE TABLE IF NOT EXISTS - NUNCA DROP
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from datetime import datetime, timezone
import uuid

# Import base to register models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Base
import models  # Import all models to register them

# Production Supabase credentials
SUPABASE_URL = "postgresql://postgres.xorxplnzfdnmuiecgvtt:lpCYw8QVXy6DR0dA@aws-0-us-west-2.pooler.supabase.com:6543/postgres"

def check_table_exists(engine, table_name):
    """Check if table exists"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def recreate_tables(engine):
    """Recreate missing tables - ADDITIVE ONLY"""
    print("🔥 STARTING TABLE RECOVERY - ADDITIVE MODE ONLY")
    print(f"⏰ {datetime.now(timezone.utc).isoformat()}")
    
    # Check which tables exist
    print("\n📊 Checking existing tables...")
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"✅ Found {len(existing_tables)} tables: {existing_tables}")
    
    # Tables we need
    required_tables = [
        'users', 'teams', 'user_agent_assignments',
        'epics', 'epic_tasks', 'epic_progress_history',
        'transcripts', 'transcript_versions', 'agent_auth'
    ]
    
    missing_tables = [t for t in required_tables if t not in existing_tables]
    
    if missing_tables:
        print(f"\n⚠️  Missing tables: {missing_tables}")
        print("🔧 Creating missing tables with CREATE TABLE IF NOT EXISTS...")
        
        # Use SQLAlchemy to create ONLY missing tables
        Base.metadata.create_all(bind=engine, checkfirst=True)
        
        print("✅ Tables created (checkfirst=True ensures no drops)")
    else:
        print("\n✅ All required tables already exist!")
    
    return missing_tables

def seed_initial_data(engine):
    """Seed initial data - IDEMPOTENT"""
    print("\n🌱 Seeding initial data...")
    
    with engine.connect() as conn:
        # Check if users already exist
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        
        if user_count > 0:
            print(f"✅ Users already exist ({user_count} users) - skipping seed")
            return
        
        print("📝 Inserting initial users...")
        
        # Insert users (IDEMPOTENT via ON CONFLICT DO NOTHING)
        conn.execute(text("""
            INSERT INTO users (email, username, full_name, hashed_password, role, active, created_at, updated_at)
            VALUES 
                ('padawan@ops.com', 'padawan', 'Padawan (Esteban Lozada)', 'padawan123', 'admin', true, NOW(), NOW()),
                ('hanslanda@ops.com', 'hanslanda', 'Hans Landa 🎬', 'hans123', 'leader', true, NOW(), NOW()),
                ('marcel@ops.com', 'marcel', 'Marcel 🎬', 'marcel123', 'member', true, NOW(), NOW()),
                ('shosanna@ops.com', 'shosanna', 'Shosanna 🔥', 'shosanna123', 'member', true, NOW(), NOW())
            ON CONFLICT (email) DO NOTHING
        """))
        
        print("✅ Users created")
        
        # Insert teams
        print("📝 Inserting teams...")
        
        # Get a project_id (assume operations project exists)
        result = conn.execute(text("SELECT id FROM projects WHERE slug = 'operations' LIMIT 1"))
        project_row = result.first()
        
        if project_row:
            project_id = project_row[0]
            
            conn.execute(text(f"""
                INSERT INTO teams (name, description, project_id, created_at, updated_at)
                VALUES 
                    ('Core Team', 'Equipo principal de Operations Dashboard', {project_id}, NOW(), NOW()),
                    ('Backend Team', 'Equipo de desarrollo backend', {project_id}, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """))
            
            print("✅ Teams created")
        else:
            print("⚠️  No operations project found - skipping teams")
        
        # Insert agent auth keys
        print("📝 Inserting agent API keys...")
        
        agents = [
            ('padawan', str(uuid.uuid4())),
            ('hanslanda', str(uuid.uuid4())),
            ('marcel', str(uuid.uuid4())),
            ('shosanna', str(uuid.uuid4()))
        ]
        
        for agent_name, api_key in agents:
            conn.execute(text(f"""
                INSERT INTO agent_auth (agent_name, api_key, permissions, rate_limit_per_minute, active, created_at, updated_at)
                VALUES 
                    ('{agent_name}', '{api_key}', 'read:tasks,write:tasks,read:projects,write:transcripts', 60, true, NOW(), NOW())
                ON CONFLICT (agent_name) DO NOTHING
            """))
        
        print("✅ Agent API keys created")
        print("\n🔑 API Keys:")
        for agent_name, api_key in agents:
            print(f"   {agent_name}: {api_key}")
        
        conn.commit()

def verify_recovery(engine):
    """Verify all tables and data"""
    print("\n🔍 Verifying recovery...")
    
    with engine.connect() as conn:
        # Check tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✅ Total tables: {len(tables)}")
        
        # Check users
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        print(f"✅ Users: {user_count}")
        
        # Check teams
        result = conn.execute(text("SELECT COUNT(*) FROM teams"))
        team_count = result.scalar()
        print(f"✅ Teams: {team_count}")
        
        # Check agent auth
        result = conn.execute(text("SELECT COUNT(*) FROM agent_auth"))
        auth_count = result.scalar()
        print(f"✅ Agent API keys: {auth_count}")
        
        # Check epics structure
        result = conn.execute(text("SELECT COUNT(*) FROM epics"))
        epic_count = result.scalar()
        print(f"✅ Epics: {epic_count}")
        
        # Check transcripts structure
        result = conn.execute(text("SELECT COUNT(*) FROM transcripts"))
        transcript_count = result.scalar()
        print(f"✅ Transcripts: {transcript_count}")

def main():
    print("=" * 60)
    print("🔥 SHOSANNA - TABLE RECOVERY SCRIPT")
    print("=" * 60)
    print("\n⚠️  CRITICAL RULES:")
    print("   ❌ NO DROP TABLE")
    print("   ❌ NO DROP DATABASE")
    print("   ❌ NO TRUNCATE")
    print("   ✅ CREATE TABLE IF NOT EXISTS only")
    print("   ✅ Additive migrations only")
    print("=" * 60)
    
    # Connect to production
    print(f"\n🔌 Connecting to Supabase production...")
    engine = create_engine(SUPABASE_URL, echo=False)
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version[:50]}...")
        
        # Recreate missing tables
        missing = recreate_tables(engine)
        
        # Seed initial data
        seed_initial_data(engine)
        
        # Verify
        verify_recovery(engine)
        
        print("\n" + "=" * 60)
        print("✅ RECOVERY COMPLETE")
        print("=" * 60)
        
        if missing:
            print(f"\n📋 Recreated tables: {missing}")
        else:
            print("\n📋 No tables were missing")
        
        print("\n🚀 Next steps:")
        print("   1. Deploy to Railway: cd backend && railway up --detach")
        print("   2. Verify endpoints:")
        print("      curl https://ops-backend-production-e8ce.up.railway.app/api/v1/users")
        print("      curl https://ops-backend-production-e8ce.up.railway.app/api/v1/epics")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
