#!/usr/bin/env python3
"""
Ejecutar migración 004: Sistema de Épicas M2M

IMPORTANTE:
- Esta migración NO hace DROP TABLE
- Hace backup de tablas viejas renombrándolas
- Crea nueva estructura M2M
- Migra datos de épicas viejas (solo metadata)

USO:
    python3 run_004_epics_migration.py

ROLLBACK (manual):
    Si algo sale mal, las tablas viejas están en *_old_backup
"""

import os
import sys
from pathlib import Path

# Agregar el directorio backend al path para importar database
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
    print(f"📄 Archivo: {migration_file}")
    print(f"🗄️  Base de datos: {engine.url.database}")
    print()
    
    # Leer script SQL
    sql_script = migration_file.read_text()
    
    # Ejecutar en una transacción
    try:
        with engine.begin() as conn:
            print("🚀 Ejecutando migración...")
            conn.execute(text(sql_script))
            print("✅ Migración ejecutada exitosamente")
            print()
            
            # Verificar resultados
            result = conn.execute(text("SELECT COUNT(*) FROM epics")).fetchone()
            epics_count = result[0]
            
            result = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE task_progress > 0")).fetchone()
            tasks_with_progress = result[0]
            
            result = conn.execute(text("SELECT COUNT(*) FROM epic_task_assignments")).fetchone()
            assignments_count = result[0]
            
            print("📊 Estado post-migración:")
            print(f"   - Épicas totales: {epics_count}")
            print(f"   - Tareas con progreso > 0: {tasks_with_progress}")
            print(f"   - Asociaciones épica-tarea: {assignments_count}")
            print()
            
            # Verificar si hay backups
            try:
                result = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_name LIKE '%_old_backup'"
                )).fetchall()
                
                if result:
                    print("💾 Tablas de backup creadas:")
                    for row in result:
                        print(f"   - {row[0]}")
                    print()
                    print("⚠️  Estas tablas se pueden eliminar después de validar la migración")
                    print("   (pero NO es urgente, están como backup de seguridad)")
            except:
                pass
            
            return True
            
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        print()
        print("🔙 La transacción ha sido revertida (rollback automático)")
        return False


def verify_prerequisites():
    """Verifica que se puede conectar a la BD"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            return True
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False


if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  MIGRACIÓN 004: SISTEMA DE ÉPICAS M2M")
    print("=" * 60)
    print()
    
    # Verificar pre-requisitos
    if not verify_prerequisites():
        print("❌ No se pudo conectar a la base de datos")
        sys.exit(1)
    
    # Confirmación
    print("⚠️  Esta migración va a:")
    print("   1. Agregar columna task_progress a tasks")
    print("   2. Renombrar tabla epics vieja (si existe) a epics_old_backup")
    print("   3. Crear nueva tabla epics con estructura M2M")
    print("   4. Crear tabla epic_task_assignments")
    print("   5. Migrar metadata de épicas viejas")
    print()
    print("✅ NO se perderán datos (se hace backup)")
    print("✅ NO se hace DROP TABLE")
    print()
    
    response = input("¿Continuar? [y/N]: ").strip().lower()
    if response not in ["y", "yes"]:
        print("❌ Migración cancelada")
        sys.exit(0)
    
    print()
    
    # Ejecutar migración
    success = run_migration()
    
    print()
    print("=" * 60)
    if success:
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    else:
        print("❌ MIGRACIÓN FALLÓ")
    print("=" * 60)
    print()
    
    sys.exit(0 if success else 1)
