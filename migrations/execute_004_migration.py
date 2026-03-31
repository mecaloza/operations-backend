#!/usr/bin/env python3
"""
Ejecutar migración 004 - Sistema de Épicas M2M (sin confirmación)
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import engine
from sqlalchemy import text


def run_migration():
    """Ejecuta la migración 004"""
    migration_file = Path(__file__).parent / "004_epics_m2m_system.sql"
    
    if not migration_file.exists():
        print(f"❌ Error: No se encontró {migration_file}")
        return False
    
    print("🔥 Shosanna - Ejecutando migración 004: Sistema de Épicas M2M")
    print(f"🗄️  Base de datos: {engine.url.database}")
    
    # Leer script SQL
    sql_script = migration_file.read_text()
    
    # Ejecutar
    try:
        with engine.begin() as conn:
            print("🚀 Ejecutando migración...")
            conn.execute(text(sql_script))
            print("✅ Migración ejecutada exitosamente")
            
            # Verificar resultados
            result = conn.execute(text("SELECT COUNT(*) FROM epics")).fetchone()
            epics_count = result[0]
            
            result = conn.execute(text("SELECT COUNT(*) FROM epic_task_assignments")).fetchone()
            assignments_count = result[0]
            
            print(f"📊 Épicas totales: {epics_count}")
            print(f"📊 Asociaciones épica-tarea: {assignments_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
