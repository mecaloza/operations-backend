from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from database import get_db
from models import Agent, AgentStatus, Project, Task, TaskStatus

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    total_agents = (
        db.query(func.count(Agent.id))
        .filter(Agent.status == AgentStatus.active.value)
        .scalar()
        or 0
    )
    task_counts = dict(
        db.query(Task.status, func.count(Task.id))
        .group_by(Task.status)
        .all()
    )

    tasks_by_project = (
        db.query(
            Project.id.label("project_id"),
            Project.name.label("project_name"),
            func.sum(case((Task.status == TaskStatus.backlog.value, 1), else_=0)).label("backlog"),
            func.sum(case((Task.status == TaskStatus.in_progress.value, 1), else_=0)).label("in_progress"),
            func.sum(case((Task.status == TaskStatus.done.value, 1), else_=0)).label("done"),
        )
        .outerjoin(Task, Task.project_id == Project.id)
        .group_by(Project.id, Project.name)
        .order_by(Project.id)
        .all()
    )

    return {
        "total_projects": total_projects,
        "total_agents": total_agents,
        "tasks_done": task_counts.get(TaskStatus.done.value, 0),
        "tasks_in_progress": task_counts.get(TaskStatus.in_progress.value, 0),
        "tasks_backlog": task_counts.get(TaskStatus.backlog.value, 0),
        "tasks_by_project": [
            {
                "project_id": row.project_id,
                "project_name": row.project_name,
                "backlog": row.backlog or 0,
                "in_progress": row.in_progress or 0,
                "done": row.done or 0,
            }
            for row in tasks_by_project
        ],
    }
