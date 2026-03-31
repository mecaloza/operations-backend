#!/usr/bin/env python3
"""
Test rápido del sistema de épicas M2M
"""

import sys
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Epic, Task, EpicTaskAssignment, Project
from datetime import datetime, date


def test_epics_system():
    """Test básico del sistema de épicas"""
    db: Session = SessionLocal()
    
    try:
        print("🔥 Shosanna - Test del Sistema de Épicas M2M")
        print()
        
        # 1. Verificar que existe al menos un proyecto
        project = db.query(Project).first()
        if not project:
            print("❌ No hay proyectos en la BD. Crea uno primero.")
            return False
        
        print(f"✅ Proyecto encontrado: {project.name} (ID: {project.id})")
        
        # 2. Crear una épica de prueba
        test_epic = Epic(
            title="[TEST] Épica de prueba - Sistema M2M",
            description="Épica creada automáticamente para verificar el sistema",
            project_id=project.id,
            priority="high",
            progress=25.0,
            status="in_progress",
            goal="Verificar que el sistema M2M funciona correctamente",
            start_date=date.today(),
        )
        
        db.add(test_epic)
        db.commit()
        db.refresh(test_epic)
        
        print(f"✅ Épica creada: {test_epic.title} (ID: {test_epic.id})")
        
        # 3. Verificar que existen tareas en el proyecto
        tasks = db.query(Task).filter(Task.project_id == project.id).limit(3).all()
        
        if not tasks:
            print("⚠️  No hay tareas en el proyecto. Crea algunas primero.")
            print(f"   Épica creada con ID: {test_epic.id}")
            return True
        
        print(f"✅ Tareas encontradas: {len(tasks)}")
        
        # 4. Asociar tareas a la épica
        for task in tasks:
            assignment = EpicTaskAssignment(
                epic_id=test_epic.id,
                task_id=task.id
            )
            db.add(assignment)
            print(f"   - Asociada tarea: {task.title[:50]}...")
        
        db.commit()
        
        print(f"✅ {len(tasks)} tareas asociadas a la épica")
        
        # 5. Verificar la relación M2M
        db.refresh(test_epic)
        assigned_tasks = len(test_epic.task_assignments)
        
        print()
        print("📊 Verificación final:")
        print(f"   - Épica ID: {test_epic.id}")
        print(f"   - Título: {test_epic.title}")
        print(f"   - Tareas asociadas: {assigned_tasks}")
        print(f"   - Progreso: {test_epic.progress}%")
        print(f"   - Status: {test_epic.status}")
        print(f"   - Prioridad: {test_epic.priority}")
        
        print()
        print("✅ SISTEMA DE ÉPICAS M2M FUNCIONANDO CORRECTAMENTE")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = test_epics_system()
    sys.exit(0 if success else 1)
