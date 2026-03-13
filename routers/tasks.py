from typing import Optional
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Task, TaskStatus
from schemas import TaskCreate, TaskUpdate, TaskOut, TaskStatusUpdate, BulkTaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


# Valid state transitions for task status
VALID_TRANSITIONS = {
    TaskStatus.backlog: {TaskStatus.in_progress, TaskStatus.blocked, TaskStatus.done},
    TaskStatus.in_progress: {TaskStatus.done, TaskStatus.blocked, TaskStatus.backlog},
    TaskStatus.done: {TaskStatus.backlog, TaskStatus.in_progress},
    TaskStatus.blocked: {TaskStatus.backlog, TaskStatus.in_progress},
}


def validate_status_transition(current: str, new: TaskStatus) -> bool:
    """Validate if a status transition is allowed"""
    try:
        current_status = TaskStatus(current)
    except ValueError:
        # If current status is invalid, allow any transition
        return True
    
    return new in VALID_TRANSITIONS.get(current_status, set())


@router.get("/", response_model=list[TaskOut])
def list_tasks(
    project_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    assigned_to: Optional[str] = None,
    include_old_done: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(Task)
    if project_id:
        q = q.filter(Task.project_id == project_id)
    if status:
        q = q.filter(Task.status == status.value)
    if assigned_to:
        q = q.filter(Task.assigned_to == assigned_to)
    
    # Filter out old "done" tasks (>5 days) unless explicitly requested
    if not include_old_done:
        five_days_ago = datetime.now(timezone.utc) - timedelta(days=5)
        # Exclude done tasks older than 5 days
        q = q.filter(
            (Task.status != TaskStatus.done.value) | 
            (Task.updated_at >= five_days_ago)
        )
    
    return q.order_by(Task.id).all()


@router.get("/kanban/{project_id}")
def kanban_board(project_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    board = {s.value: [] for s in TaskStatus}
    for t in tasks:
        board.setdefault(t.status, []).append(TaskOut.model_validate(t))
    return board


@router.post("/", response_model=TaskOut, status_code=201)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**data.model_dump(mode="json"))
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/bulk-update", response_model=dict)
def bulk_update_tasks(
    data: BulkTaskUpdate,
    db: Session = Depends(get_db)
):
    """
    Bulk update multiple tasks at once.
    Returns count of updated tasks and any errors.
    """
    if not data.task_ids:
        raise HTTPException(400, "task_ids cannot be empty")
    
    # Fetch all tasks
    tasks = db.query(Task).filter(Task.id.in_(data.task_ids)).all()
    
    if not tasks:
        raise HTTPException(404, "No tasks found with provided IDs")
    
    updated_count = 0
    errors = []
    
    for task in tasks:
        try:
            # Validate status transition if status is being updated
            if data.status is not None:
                if not validate_status_transition(task.status, data.status):
                    errors.append({
                        "task_id": task.id,
                        "error": f"Invalid transition: {task.status} → {data.status.value}"
                    })
                    continue
                task.status = data.status.value
            
            # Update other fields if provided
            if data.priority is not None:
                task.priority = data.priority.value
            if data.assigned_to is not None:
                task.assigned_to = data.assigned_to
            
            # Update timestamp
            task.updated_at = datetime.now(timezone.utc)
            updated_count += 1
            
        except Exception as e:
            errors.append({
                "task_id": task.id,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "updated_count": updated_count,
        "total_requested": len(data.task_ids),
        "errors": errors if errors else None
    }


@router.patch("/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int, 
    data: TaskStatusUpdate, 
    db: Session = Depends(get_db)
):
    """
    Optimized endpoint to update only task status.
    Validates state transitions and auto-updates timestamp.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    
    # Validate state transition
    if not validate_status_transition(task.status, data.status):
        raise HTTPException(
            400, 
            f"Invalid status transition: {task.status} → {data.status.value}"
        )
    
    # Update status and timestamp
    task.status = data.status.value
    task.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    for k, v in data.model_dump(exclude_unset=True, mode="json").items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    db.delete(task)
    db.commit()
