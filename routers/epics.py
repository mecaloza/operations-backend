from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from database import get_db
from models import Epic, EpicTaskAssignment, Task, Project, User, EpicEvaluationPoint
from schemas import (
    EpicCreate,
    EpicUpdate,
    EpicResponse,
    EpicDetailResponse,
    TaskResponse,
    AddTasksToEpicRequest,
    EvaluationPointResponse,
)
from routers.auth import get_current_user

router = APIRouter(tags=["Epics"])


# ========== ÉPICAS ==========


@router.get("/epics", response_model=List[EpicResponse])
def list_epics(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    min_progress: Optional[float] = None,
    max_progress: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista épicas con filtros"""
    query = db.query(Epic)

    # Filtros
    if project_id:
        query = query.filter(Epic.project_id == project_id)
    if status:
        query = query.filter(Epic.status == status)
    if min_progress is not None:
        query = query.filter(Epic.progress >= min_progress)
    if max_progress is not None:
        query = query.filter(Epic.progress <= max_progress)

    epics = query.order_by(Epic.created_at.desc()).all()

    # Agregar task_count a cada épica
    result = []
    for epic in epics:
        epic_dict = {
            "id": epic.id,
            "title": epic.title,
            "description": epic.description,
            "project_id": epic.project_id,
            "priority": epic.priority,
            "progress": epic.progress,
            "status": epic.status,
            "goal": epic.goal,
            "start_date": epic.start_date,
            "target_date": epic.target_date,
            "created_at": epic.created_at,
            "updated_at": epic.updated_at,
            "task_count": len(epic.task_assignments),
        }
        result.append(EpicResponse(**epic_dict))

    return result


@router.post("/epics", response_model=EpicResponse, status_code=201)
def create_epic(
    epic: EpicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crear nueva épica"""
    # Validar que el proyecto existe
    project = db.query(Project).filter(Project.id == epic.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    new_epic = Epic(**epic.model_dump())
    db.add(new_epic)
    db.commit()
    db.refresh(new_epic)

    # Agregar task_count
    epic_dict = {
        "id": new_epic.id,
        "title": new_epic.title,
        "description": new_epic.description,
        "project_id": new_epic.project_id,
        "priority": new_epic.priority,
        "progress": new_epic.progress,
        "status": new_epic.status,
        "goal": new_epic.goal,
        "start_date": new_epic.start_date,
        "target_date": new_epic.target_date,
        "created_at": new_epic.created_at,
        "updated_at": new_epic.updated_at,
        "task_count": 0,
    }
    return EpicResponse(**epic_dict)


@router.get("/epics/{epic_id}", response_model=EpicDetailResponse)
def get_epic(
    epic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detalle de épica con tareas y evaluation points"""
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    # Obtener tareas asociadas
    tasks = (
        db.query(Task)
        .join(EpicTaskAssignment, EpicTaskAssignment.task_id == Task.id)
        .filter(EpicTaskAssignment.epic_id == epic_id)
        .all()
    )

    # Obtener evaluation points con nombres de usuarios
    eval_points = []
    for ep in epic.evaluation_points:
        user = db.query(User).filter(User.id == ep.assigned_to).first()
        eval_points.append({
            "id": ep.id,
            "epic_id": ep.epic_id,
            "category": ep.category,
            "description": ep.description,
            "assigned_to": ep.assigned_to,
            "assigned_to_name": user.full_name if user else None,
            "progress": ep.progress,
            "weight": ep.weight,
            "created_at": ep.created_at,
            "updated_at": ep.updated_at,
        })

    # Calcular promedio de evaluation points
    avg_progress = None
    if eval_points:
        avg_progress = sum(ep["progress"] for ep in eval_points) / len(eval_points)

    epic_dict = {
        "id": epic.id,
        "title": epic.title,
        "description": epic.description,
        "project_id": epic.project_id,
        "priority": epic.priority,
        "progress": epic.progress,
        "status": epic.status,
        "goal": epic.goal,
        "start_date": epic.start_date,
        "target_date": epic.target_date,
        "created_at": epic.created_at,
        "updated_at": epic.updated_at,
        "task_count": len(tasks),
        "tasks": tasks,
        "evaluation_points": eval_points,
        "avg_evaluation_progress": avg_progress,
    }
    return EpicDetailResponse(**epic_dict)


@router.patch("/epics/{epic_id}", response_model=EpicResponse)
def update_epic(
    epic_id: int,
    updates: EpicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Actualizar épica (incluido % manual)"""
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    # Actualizar campos
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(epic, field, value)

    db.commit()
    db.refresh(epic)

    epic_dict = {
        "id": epic.id,
        "title": epic.title,
        "description": epic.description,
        "project_id": epic.project_id,
        "priority": epic.priority,
        "progress": epic.progress,
        "status": epic.status,
        "goal": epic.goal,
        "start_date": epic.start_date,
        "target_date": epic.target_date,
        "created_at": epic.created_at,
        "updated_at": epic.updated_at,
        "task_count": len(epic.task_assignments),
    }
    return EpicResponse(**epic_dict)


@router.delete("/epics/{epic_id}", status_code=204)
def delete_epic(
    epic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Eliminar épica (tareas quedan orphan)"""
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    # Las asociaciones se eliminan automáticamente por CASCADE
    # Las tareas NO se eliminan (quedan orphan)
    db.delete(epic)
    db.commit()
    return


# ========== ASOCIACIÓN TAREAS <-> ÉPICAS ==========


@router.post("/epics/{epic_id}/tasks", status_code=201)
def add_tasks_to_epic(
    epic_id: int,
    request: AddTasksToEpicRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Asociar múltiples tareas a épica"""
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    added_count = 0
    errors = []

    for task_id in request.task_ids:
        # Verificar que la tarea existe
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            errors.append(f"Task {task_id} not found")
            continue

        # Verificar que no exista ya la asociación
        existing = (
            db.query(EpicTaskAssignment)
            .filter(
                EpicTaskAssignment.epic_id == epic_id,
                EpicTaskAssignment.task_id == task_id,
            )
            .first()
        )
        if existing:
            errors.append(f"Task {task_id} already assigned to epic {epic_id}")
            continue

        # Crear asociación
        assignment = EpicTaskAssignment(epic_id=epic_id, task_id=task_id)
        db.add(assignment)
        added_count += 1

    db.commit()

    return {
        "message": f"Added {added_count} tasks to epic {epic_id}",
        "added_count": added_count,
        "errors": errors if errors else None,
    }


@router.delete("/epics/{epic_id}/tasks/{task_id}", status_code=204)
def remove_task_from_epic(
    epic_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Desasociar tarea de épica"""
    assignment = (
        db.query(EpicTaskAssignment)
        .filter(
            EpicTaskAssignment.epic_id == epic_id,
            EpicTaskAssignment.task_id == task_id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404, detail="Task not assigned to this epic"
        )

    db.delete(assignment)
    db.commit()
    return


@router.get("/epics/{epic_id}/tasks", response_model=List[TaskResponse])
def get_epic_tasks(
    epic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar tareas de una épica"""
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    tasks = (
        db.query(Task)
        .join(EpicTaskAssignment, EpicTaskAssignment.task_id == Task.id)
        .filter(EpicTaskAssignment.epic_id == epic_id)
        .all()
    )

    return tasks
