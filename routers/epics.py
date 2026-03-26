from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Epic, EpicTask, Project, EpicProgressHistory
from schemas import (
    EpicCreate,
    EpicUpdate,
    EpicOut,
    EpicTaskCreate,
    EpicTaskUpdate,
    EpicTaskOut,
    SprintReport,
    SprintEpic,
    SprintEpicTask,
)

router = APIRouter(tags=["Epics"])


def _recalculate_epic_progress(db: Session, epic_id: int):
    """Recalcula el % de avance de una épica basado en sus sub-tareas."""
    epic = db.query(Epic).filter(Epic.id == epic_id, Epic.deleted == False).first()
    if not epic:
        return

    tasks = db.query(EpicTask).filter(
        EpicTask.epic_id == epic_id, EpicTask.deleted == False
    ).all()

    if not tasks:
        epic.calculated_progress = 0.0
    else:
        total_progress = sum(task.progress for task in tasks)
        epic.calculated_progress = round(total_progress / len(tasks), 2)

    db.commit()
    db.refresh(epic)


def _save_progress_snapshot(db: Session, epic_id: int):
    """Guarda un snapshot del progreso actual de la épica para historial."""
    epic = db.query(Epic).filter(Epic.id == epic_id, Epic.deleted == False).first()
    if epic:
        snapshot = EpicProgressHistory(epic_id=epic.id, progress=epic.calculated_progress)
        db.add(snapshot)
        db.commit()


# ========== ÉPICAS ==========


@router.get("/epics", response_model=List[EpicOut])
def list_epics(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lista épicas. Puede filtrar por project_id y/o status."""
    query = db.query(Epic).filter(Epic.deleted == False)

    if project_id:
        query = query.filter(Epic.project_id == project_id)
    if status:
        query = query.filter(Epic.status == status)

    return query.order_by(Epic.created_at.desc()).all()


@router.post("/epics", response_model=EpicOut, status_code=201)
def create_epic(epic: EpicCreate, db: Session = Depends(get_db)):
    """Crea una nueva épica."""
    # Validar que el proyecto existe
    project = db.query(Project).filter(Project.id == epic.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    new_epic = Epic(**epic.model_dump())
    db.add(new_epic)
    db.commit()
    db.refresh(new_epic)
    return new_epic


@router.get("/epics/{epic_id}", response_model=EpicOut)
def get_epic(epic_id: int, db: Session = Depends(get_db)):
    """Obtiene una épica por ID."""
    epic = db.query(Epic).filter(Epic.id == epic_id, Epic.deleted == False).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    return epic


@router.patch("/epics/{epic_id}", response_model=EpicOut)
def update_epic(epic_id: int, updates: EpicUpdate, db: Session = Depends(get_db)):
    """Actualiza una épica."""
    epic = db.query(Epic).filter(Epic.id == epic_id, Epic.deleted == False).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(epic, field, value)

    db.commit()
    db.refresh(epic)
    return epic


@router.delete("/epics/{epic_id}", status_code=204)
def delete_epic(epic_id: int, db: Session = Depends(get_db)):
    """Soft delete de una épica."""
    epic = db.query(Epic).filter(Epic.id == epic_id, Epic.deleted == False).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    epic.deleted = True
    db.commit()
    return


# ========== SUB-TAREAS ==========


@router.get("/epics/{epic_id}/tasks", response_model=List[EpicTaskOut])
def list_epic_tasks(epic_id: int, db: Session = Depends(get_db)):
    """Lista todas las sub-tareas de una épica."""
    epic = db.query(Epic).filter(Epic.id == epic_id, Epic.deleted == False).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    tasks = (
        db.query(EpicTask)
        .filter(EpicTask.epic_id == epic_id, EpicTask.deleted == False)
        .order_by(EpicTask.created_at)
        .all()
    )
    return tasks


@router.post("/epics/{epic_id}/tasks", response_model=EpicTaskOut, status_code=201)
def create_epic_task(
    epic_id: int, task: EpicTaskCreate, db: Session = Depends(get_db)
):
    """Crea una sub-tarea dentro de una épica."""
    epic = db.query(Epic).filter(Epic.id == epic_id, Epic.deleted == False).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    new_task = EpicTask(epic_id=epic_id, **task.model_dump())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # Recalcular progreso de la épica
    _recalculate_epic_progress(db, epic_id)

    return new_task


@router.patch("/epic-tasks/{task_id}", response_model=EpicTaskOut)
def update_epic_task(
    task_id: int, updates: EpicTaskUpdate, db: Session = Depends(get_db)
):
    """Actualiza una sub-tarea (%, estado, asignado)."""
    task = db.query(EpicTask).filter(EpicTask.id == task_id, EpicTask.deleted == False).first()
    if not task:
        raise HTTPException(status_code=404, detail="Epic task not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    # Recalcular progreso de la épica
    _recalculate_epic_progress(db, task.epic_id)
    _save_progress_snapshot(db, task.epic_id)

    return task


@router.delete("/epic-tasks/{task_id}", status_code=204)
def delete_epic_task(task_id: int, db: Session = Depends(get_db)):
    """Soft delete de una sub-tarea."""
    task = db.query(EpicTask).filter(EpicTask.id == task_id, EpicTask.deleted == False).first()
    if not task:
        raise HTTPException(status_code=404, detail="Epic task not found")

    epic_id = task.epic_id
    task.deleted = True
    db.commit()

    # Recalcular progreso de la épica
    _recalculate_epic_progress(db, epic_id)

    return


# ========== REPORTES ==========


@router.get("/projects/{project_id}/sprint-report", response_model=SprintReport)
def get_sprint_report(project_id: int, db: Session = Depends(get_db)):
    """Reporte completo de avance: épicas + sub-tareas + % total."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    epics = (
        db.query(Epic)
        .filter(Epic.project_id == project_id, Epic.deleted == False)
        .order_by(Epic.created_at)
        .all()
    )

    sprint_epics = []
    total_progress_sum = 0.0

    for epic in epics:
        tasks = (
            db.query(EpicTask)
            .filter(EpicTask.epic_id == epic.id, EpicTask.deleted == False)
            .order_by(EpicTask.created_at)
            .all()
        )

        sprint_tasks = [
            SprintEpicTask(
                title=t.title,
                progress=t.progress,
                assigned_to=t.assigned_to,
                status=t.status,
            )
            for t in tasks
        ]

        sprint_epics.append(
            SprintEpic(
                id=epic.id,
                title=epic.title,
                progress=epic.calculated_progress,
                target_progress=epic.target_progress,
                status=epic.status,
                tasks=sprint_tasks,
            )
        )

        total_progress_sum += epic.calculated_progress

    total_progress = round(total_progress_sum / len(epics), 2) if epics else 0.0

    return SprintReport(
        project_id=project.id,
        project_name=project.name,
        total_progress=total_progress,
        epics=sprint_epics,
    )
