"""
Agent API Router - API específica para agentes AI
Autenticación vía X-Agent-API-Key header
Rate limiting por minuto
"""
from fastapi import APIRouter, Depends, HTTPException, Header, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid

from database import get_db
from models import AgentAuth, Task, Project, Epic, EpicTask, Transcript
from schemas import (
    AgentAuthCreate, AgentAuthOut, AgentAuthUpdate,
    TaskOut, ProjectOut, EpicTaskOut,
    TaskStatusUpdate, TranscriptOut, TranscriptCreate
)


router = APIRouter(prefix="/agent-api", tags=["Agent API"])


# --- Rate Limiting Storage (in-memory simple implementation) ---
# En producción usar Redis o similar
rate_limit_tracker: dict[str, list[datetime]] = {}


def check_rate_limit(agent_auth: AgentAuth) -> bool:
    """Check if agent is within rate limit"""
    now = datetime.now(timezone.utc)
    minute_ago = now - timedelta(minutes=1)
    
    # Limpiar requests antiguos
    if agent_auth.api_key in rate_limit_tracker:
        rate_limit_tracker[agent_auth.api_key] = [
            ts for ts in rate_limit_tracker[agent_auth.api_key] 
            if ts > minute_ago
        ]
    else:
        rate_limit_tracker[agent_auth.api_key] = []
    
    # Verificar límite
    current_count = len(rate_limit_tracker[agent_auth.api_key])
    if current_count >= agent_auth.rate_limit_per_minute:
        return False
    
    # Registrar request actual
    rate_limit_tracker[agent_auth.api_key].append(now)
    return True


def get_agent_auth(
    x_agent_api_key: str = Header(..., alias="X-Agent-API-Key"),
    db: Session = Depends(get_db)
) -> AgentAuth:
    """
    Dependency para autenticar agente vía API key
    Valida:
    - Existencia del API key
    - Estado activo
    - Rate limiting
    """
    # Buscar agent auth
    agent_auth = db.query(AgentAuth).filter(
        AgentAuth.api_key == x_agent_api_key
    ).first()
    
    if not agent_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    if not agent_auth.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent is inactive"
        )
    
    # Rate limiting
    if not check_rate_limit(agent_auth):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {agent_auth.rate_limit_per_minute} requests per minute"
        )
    
    # Actualizar last_access
    agent_auth.last_access = datetime.now(timezone.utc)
    db.commit()
    
    return agent_auth


def check_permission(agent_auth: AgentAuth, required_permission: str) -> bool:
    """Check if agent has required permission"""
    permissions = [p.strip() for p in agent_auth.permissions.split(",")]
    return required_permission in permissions


# --- Authentication Endpoints ---

@router.post("/auth/register", response_model=AgentAuthOut)
def register_agent(
    data: AgentAuthCreate,
    db: Session = Depends(get_db)
):
    """
    Registrar nuevo agente y generar API key
    """
    # Verificar que no exista ya
    existing = db.query(AgentAuth).filter(
        AgentAuth.agent_name == data.agent_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent {data.agent_name} already registered"
        )
    
    # Crear nuevo agent auth
    agent_auth = AgentAuth(
        agent_name=data.agent_name,
        api_key=str(uuid.uuid4()),
        permissions=data.permissions or "read:tasks,write:tasks,read:projects"
    )
    
    db.add(agent_auth)
    db.commit()
    db.refresh(agent_auth)
    
    return agent_auth


@router.get("/auth/me", response_model=AgentAuthOut)
def get_current_agent(
    agent_auth: AgentAuth = Depends(get_agent_auth)
):
    """
    Obtener información del agente autenticado
    """
    return agent_auth


@router.get("/auth/test")
def test_auth(
    agent_auth: AgentAuth = Depends(get_agent_auth)
):
    """
    Endpoint de testing para verificar autenticación
    """
    return {
        "authenticated": True,
        "agent_name": agent_auth.agent_name,
        "permissions": agent_auth.permissions.split(","),
        "rate_limit": agent_auth.rate_limit_per_minute,
        "last_access": agent_auth.last_access
    }


# --- Task Endpoints ---

@router.get("/tasks/assigned", response_model=List[TaskOut])
def get_assigned_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    agent_auth: AgentAuth = Depends(get_agent_auth),
    db: Session = Depends(get_db)
):
    """
    Obtener tareas asignadas al agente (filtrable)
    Requiere: read:tasks
    """
    if not check_permission(agent_auth, "read:tasks"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing permission: read:tasks"
        )
    
    # Query base: tareas asignadas a este agente
    query = db.query(Task).filter(
        Task.assigned_to == agent_auth.agent_name
    )
    
    # Aplicar filtros
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    return tasks


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task_detail(
    task_id: int,
    agent_auth: AgentAuth = Depends(get_agent_auth),
    db: Session = Depends(get_db)
):
    """
    Obtener detalle de una tarea específica
    Requiere: read:tasks
    """
    if not check_permission(agent_auth, "read:tasks"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing permission: read:tasks"
        )
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    return task


@router.patch("/tasks/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int,
    data: TaskStatusUpdate,
    agent_auth: AgentAuth = Depends(get_agent_auth),
    db: Session = Depends(get_db)
):
    """
    Actualizar estado de una tarea
    Requiere: write:tasks
    """
    if not check_permission(agent_auth, "write:tasks"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing permission: write:tasks"
        )
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    # Verificar que la tarea esté asignada al agente
    if task.assigned_to != agent_auth.agent_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Task not assigned to this agent"
        )
    
    task.status = data.status
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    
    return task


# --- Project Endpoints ---

@router.get("/projects", response_model=List[ProjectOut])
def get_projects(
    agent_auth: AgentAuth = Depends(get_agent_auth),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de proyectos disponibles
    Requiere: read:projects
    """
    if not check_permission(agent_auth, "read:projects"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing permission: read:projects"
        )
    
    projects = db.query(Project).all()
    return projects


# --- Epic Endpoints ---

@router.get("/epics/{epic_id}/tasks", response_model=List[EpicTaskOut])
def get_epic_tasks(
    epic_id: int,
    agent_auth: AgentAuth = Depends(get_agent_auth),
    db: Session = Depends(get_db)
):
    """
    Obtener sub-tareas de una épica
    Requiere: read:epics
    """
    if not check_permission(agent_auth, "read:epics"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing permission: read:epics"
        )
    
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Epic {epic_id} not found"
        )
    
    tasks = db.query(EpicTask).filter(
        EpicTask.epic_id == epic_id,
        EpicTask.deleted == False
    ).all()
    
    return tasks


# --- Transcript Endpoints ---

@router.get("/transcripts/{transcript_id}", response_model=TranscriptOut)
def get_transcript(
    transcript_id: int,
    agent_auth: AgentAuth = Depends(get_agent_auth),
    db: Session = Depends(get_db)
):
    """
    Descargar transcript completo
    Requiere: read:transcripts
    """
    if not check_permission(agent_auth, "read:transcripts"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing permission: read:transcripts"
        )
    
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.is_latest == True
    ).first()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript {transcript_id} not found"
        )
    
    t_dict = TranscriptOut.model_validate(transcript).model_dump()
    t_dict["related_task"] = transcript.task
    t_dict["related_epic"] = transcript.epic
    
    return TranscriptOut(**t_dict)


@router.get("/tasks/{task_id}/context")
def get_task_context(
    task_id: int,
    agent_auth: AgentAuth = Depends(get_agent_auth),
    db: Session = Depends(get_db)
):
    """
    Devuelve tarea + transcripts + épica relacionada (contexto completo)
    Requiere: read:tasks, read:transcripts
    """
    if not check_permission(agent_auth, "read:tasks"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing permission: read:tasks"
        )
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    # Obtener transcripts de la tarea
    transcripts = []
    if check_permission(agent_auth, "read:transcripts"):
        transcripts = db.query(Transcript).filter(
            Transcript.task_id == task_id,
            Transcript.is_latest == True
        ).all()
    
    # Obtener épica relacionada (si existe)
    epic = None
    if task.epic_id:
        epic = db.query(Epic).filter(Epic.id == task.epic_id).first()
    
    return {
        "task": TaskOut.model_validate(task),
        "transcripts": [TranscriptOut.model_validate(t) for t in transcripts],
        "epic": epic if epic else None
    }


@router.post("/transcripts", response_model=TranscriptOut, status_code=201)
def create_transcript_from_agent(
    data: TranscriptCreate,
    agent_auth: AgentAuth = Depends(get_agent_auth),
    db: Session = Depends(get_db)
):
    """
    Crear transcript desde agente
    Requiere: write:transcripts
    """
    if not check_permission(agent_auth, "write:transcripts"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing permission: write:transcripts"
        )
    
    # Validaciones básicas
    if not data.task_id and not data.epic_id:
        raise HTTPException(
            status_code=400,
            detail="Al menos uno de task_id o epic_id debe estar presente"
        )
    
    if not data.title.strip() or not data.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Título y contenido son obligatorios"
        )
    
    # Crear transcript
    from models import TranscriptVersion
    
    file_size = len(data.content.encode('utf-8'))
    
    transcript = Transcript(
        title=data.title,
        content=data.content,
        task_id=data.task_id,
        epic_id=data.epic_id,
        project_id=data.project_id,
        created_by=data.created_by or agent_auth.agent_name,
        tags=data.tags or "",
        file_size=file_size,
        version=1,
        is_latest=True
    )
    
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    
    # Crear versión inicial
    version = TranscriptVersion(
        transcript_id=transcript.id,
        version=1,
        content=data.content,
        changed_by=data.created_by or agent_auth.agent_name,
        change_summary="Versión inicial"
    )
    db.add(version)
    db.commit()
    db.refresh(transcript)
    
    t_dict = TranscriptOut.model_validate(transcript).model_dump()
    t_dict["related_task"] = transcript.task
    t_dict["related_epic"] = transcript.epic
    
    return TranscriptOut(**t_dict)
